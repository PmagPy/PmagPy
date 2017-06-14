#!/usr/bin/env pythonw

# pylint: disable=W0612,C0111,C0103,W0201,E402

print("-I- Importing Pmag GUI dependencies")
#from pmag_env import set_env
#set_env.set_backend(wx=True)
import matplotlib
if not matplotlib.get_backend() == 'WXAgg':
    matplotlib.use('WXAgg')
import wx
import wx.lib.buttons as buttons
import wx.lib.newevent as newevent
import os
import sys
import webbrowser

from pmagpy import pmag
from pmagpy import ipmag
from pmagpy import builder2 as builder
from pmagpy import new_builder as nb
from dialogs import pmag_basic_dialogs_native3 as pbd3
from dialogs import pmag_basic_dialogs as pbd2
from dialogs import pmag_er_magic_dialogs
from dialogs import pmag_gui_menu3 as pmag_gui_menu
from dialogs import ErMagicBuilder
from dialogs import demag_dialogs
from dialogs import pmag_widgets as pw

global PMAGPY_DIRECTORY
import pmagpy.find_pmag_dir as find_pmag_dir
PMAGPY_DIRECTORY = find_pmag_dir.get_pmag_dir()

from programs import demag_gui
from programs import thellier_gui


class MagMainFrame(wx.Frame):
    """"""
    try:
        version= pmag.get_version()
    except:
        version = ""
    title = "Pmag GUI   version: %s"%version
    if sys.platform in ['win32', 'win64']:
        title += "   Powered by Enthought Canopy"

    def __init__(self, WD=None, DM=None, dmodel=None):
        """
        Input working directory, data model number (2.5 or 3),
        and data model (optional).
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title, name='pmag_gui mainframe')

        #set icon
        self.icon = wx.Icon()
        icon_path = os.path.join(PMAGPY_DIRECTORY, 'programs', 'images', 'PmagPy.ico')
        if os.path.isfile(icon_path):
            self.icon.CopyFromBitmap(wx.Bitmap(icon_path, wx.BITMAP_TYPE_ANY))
            self.SetIcon(self.icon)
        else:
            print("-I- PmagPy icon file not found -- skipping")

        # if DM was provided:
        if DM:
            self.data_model_num = int(float(DM))
        # try to get DM from command line args
        if not DM:
            self.data_model_num = int(float(pmag.get_named_arg_from_sys("-DM", 0)))
            DM = self.data_model_num

        # if WD was provided:
        if WD:
            self.WD = WD
        else:
            WD = pmag.get_named_arg_from_sys("-WD", '')
            self.WD = WD

        self.data_model = dmodel
        self.FIRST_RUN = True

        self.panel = wx.Panel(self, name='pmag_gui main panel')
        self.InitUI()

        if WD and DM:
            self.set_dm(self.data_model_num)
        if WD:
            self.dir_path.SetValue(self.WD)


        # for use as module:
        self.resource_dir = os.getcwd()

        # set some things
        self.HtmlIsOpen = False
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)

        # if not specified on the command line,
        # make the user choose data model num (2 or 3)
        # and working directory
        wx.CallAfter(self.get_dm_and_wd, DM, WD)

    def get_dm_and_wd(self, DM=None, WD=None):
        """
        If DM and/or WD are missing, call user-input dialogs
        to ascertain that information.

        Parameters
        ----------
        self
        DM : int
            number of data model to use (2 or 3), default None
        WD : str
            name of working directory, default None
        """
        if not DM:
            self.get_dm_num()
        if not WD:
            self.get_DIR()
            # no need to get wd_data
            return
        if self.data_model_num == 2:
            self.get_wd_data2()
        else:
            self.get_wd_data()

    def get_dm_num(self):
        """
        Show dialog to get user input for which data model to use,
        2 or 3.
        Set self.data_model_num, and create 3.0 contribution or
        2.5 ErMagicBuilder as needed.
        """
        ui_dialog = demag_dialogs.user_input(self,['data_model'],
                                             parse_funcs=[float],
                                             heading="Please input prefered data model (2.5,3.0).  Note: 2.5 is for legacy projects only, if you have new data OR if you want to upgrade your old data, please use 3.0.",
                                             values=[3])
        # figure out where to put this
        res = ui_dialog.ShowModal()
        vals = ui_dialog.get_values()
        self.data_model_num = int(vals[1]['data_model'])
        #
        if self.data_model_num not in (2, 3):
            pw.simple_warning("Input data model not recognized, defaulting to 3")
            self.data_model_num = 3
        self.set_dm(self.data_model_num)

    def set_dm(self, num):
        """
        Make GUI changes based on data model num.
        Get info from WD in appropriate format
        """
        #enable or disable self.btn1a
        if self.data_model_num == 3:
            self.btn1a.Enable()
        else:
            self.btn1a.Disable()
        #
        # set pmag_basic_dialogs
        global pmag_basic_dialogs
        if self.data_model_num == 2:
            pmag_basic_dialogs = pbd2
            #wx.CallAfter(self.get_wd_data2)
        elif self.data_model_num == 3:
            pmag_basic_dialogs = pbd3
            #wx.CallAfter(self.get_wd_data)

        # do / re-do menubar
        menubar = pmag_gui_menu.MagICMenu(self, data_model_num=self.data_model_num)
        self.SetMenuBar(menubar)

    def get_wd_data(self):
        """
        Show dialog to get user input for which directory
        to set as working directory.
        """
        wait = wx.BusyInfo('Reading in data from current working directory, please wait...')
        #wx.Yield()
        print('-I- Read in any available data from working directory')
        self.contribution = nb.Contribution(self.WD, dmodel=self.data_model)
        del wait

    def get_wd_data2(self):
        wait = wx.BusyInfo('Reading in data from current working directory, please wait...')
        #wx.Yield()
        print('-I- Read in any available data from working directory (data model 2)')

        self.er_magic = builder.ErMagicBuilder(self.WD,
                                               data_model=self.data_model)
        del wait

    def InitUI(self):
        menubar = pmag_gui_menu.MagICMenu(self, data_model_num=self.data_model_num)
        self.SetMenuBar(menubar)

        #pnl = self.panel

        #---sizer logo ----

        #start_image = wx.Image("/Users/ronshaar/PmagPy/images/logo2.png")
        #start_image = wx.Image("/Users/Python/simple_examples/001.png")
        #start_image.Rescale(start_image.GetWidth(), start_image.GetHeight())
        #image = wx.BitmapFromImage(start_image)
        #self.logo = wx.StaticBitmap(self.panel, -1, image)


        #---sizer 0 ----

        bSizer0 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Choose MagIC project directory"), wx.HORIZONTAL)
        self.dir_path = wx.TextCtrl(self.panel, id=-1, size=(600,25), style=wx.TE_READONLY)
        self.change_dir_button = buttons.GenButton(self.panel, id=-1, label="change directory",size=(-1, -1))
        self.change_dir_button.SetBackgroundColour("#F8F8FF")
        self.change_dir_button.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_change_dir_button, self.change_dir_button)
        bSizer0.Add(self.change_dir_button, wx.ALIGN_LEFT)
        bSizer0.AddSpacer(40)
        bSizer0.Add(self.dir_path,wx.ALIGN_CENTER_VERTICAL)

        # not fully implemented method for saving/reverting WD
        # last saved: []
        #bSizer0_1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "Save MagIC project directory in current state or revert to last-saved state" ), wx.HORIZONTAL )
        #saved_label = wx.StaticText(self.panel, -1, "Last saved:", (20, 120))
        #self.last_saved_time = wx.TextCtrl(self.panel, id=-1, size=(100,25), style=wx.TE_READONLY)
        #now = datetime.datetime.now()
        #now_string = "{}:{}:{}".format(now.hour, now.minute, now.second)
        #self.last_saved_time.write(now_string)
        #self.save_dir_button = buttons.GenButton(self.panel, id=-1, label = "save dir", size=(-1, -1))
        #self.revert_dir_button = buttons.GenButton(self.panel, id=-1, label = "revert dir", size=(-1, -1))

        #self.Bind(wx.EVT_BUTTON, self.on_revert_dir_button, self.revert_dir_button)
        #self.Bind(wx.EVT_BUTTON, self.on_save_dir_button, self.save_dir_button)


        #bSizer0_1.Add(saved_label, flag=wx.RIGHT, border=10)
        #bSizer0_1.Add(self.last_saved_time, flag=wx.RIGHT, border=10)
        #bSizer0_1.Add(self.save_dir_button,flag=wx.ALIGN_LEFT|wx.RIGHT, border=10)
        #bSizer0_1.Add(self.revert_dir_button,wx.ALIGN_LEFT)

        #
        #---sizer 1 ----
        bSizer1 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Import data to working directory"), wx.HORIZONTAL)

        text = "1. Convert magnetometer files to MagIC format"
        self.btn1 = buttons.GenButton(self.panel, id=-1, label=text,
                                      size=(450, 50), name='step 1')
        self.btn1.SetBackgroundColour("#FDC68A")
        self.btn1.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_convert_file, self.btn1)

        text = "2. (optional) Calculate geographic/tilt-corrected directions"
        self.btn2 = buttons.GenButton(self.panel, id=-1, label=text, size=(450, 50), name='step 2')
        self.btn2.SetBackgroundColour("#FDC68A")
        self.btn2.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_orientation_button, self.btn2)
        text = "3. (optional) Add MagIC metadata for uploading data to MagIC "
        self.btn3 = buttons.GenButton(self.panel, id=-1, label=text, size=(450, 50), name='step 3')
        self.btn3.SetBackgroundColour("#FDC68A")
        self.btn3.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_er_data, self.btn3)

        text = "Unpack txt file downloaded from MagIC"
        self.btn4 = buttons.GenButton(self.panel, id=-1, label=text, size=(330, 50))
        self.btn4.SetBackgroundColour("#FDC68A")
        self.btn4.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_unpack, self.btn4)


        text = "Convert directory to 3.0. format (legacy data only)"
        self.btn1a = buttons.GenButton(self.panel, id=-1, label=text,
                                       size=(330, 50), name='step 1a')
        self.btn1a.SetBackgroundColour("#FDC68A")
        self.btn1a.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_convert_3, self.btn1a)

        #str = "OR"
        OR = wx.StaticText(self.panel, -1, "or", (20, 120))
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)
        OR.SetFont(font)


        #bSizer0.Add(self.panel,self.btn1,wx.ALIGN_TOP)
        bSizer1_1 = wx.BoxSizer(wx.VERTICAL)
        bSizer1_1.AddSpacer(20)
        bSizer1_1.Add(self.btn1, wx.ALIGN_TOP)
        bSizer1_1.AddSpacer(20)
        bSizer1_1.Add(self.btn2, wx.ALIGN_TOP)
        bSizer1_1.AddSpacer(20)
        bSizer1_1.Add(self.btn3, wx.ALIGN_TOP)
        bSizer1_1.AddSpacer(20)

        bSizer1.Add(bSizer1_1, wx.ALIGN_CENTER, wx.EXPAND)
        bSizer1.AddSpacer(20)

        bSizer1.Add(OR, 0, wx.ALIGN_CENTER, 0)
        bSizer1.AddSpacer(20)

        bSizer1_2 = wx.BoxSizer(wx.VERTICAL)
        spacing = 60 #if self.data_model_num == 3 else 90
        bSizer1_2.AddSpacer(spacing)

        bSizer1_2.Add(self.btn4, 0, wx.ALIGN_CENTER, 0)
        bSizer1_2.AddSpacer(20)
        bSizer1_2.Add(self.btn1a, 0, wx.ALIGN_CENTER, 0)
        bSizer1_2.AddSpacer(20)

        bSizer1.Add(bSizer1_2)
        bSizer1.AddSpacer(20)

        #---sizer 2 ----
        bSizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Analysis and plots" ), wx.HORIZONTAL)

        text = "Demag GUI"
        self.btn_demag_gui = buttons.GenButton(self.panel, id=-1, label=text, size=(300, 50), name='demag gui')
        self.btn_demag_gui.SetBackgroundColour("#6ECFF6")
        self.btn_demag_gui.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_run_demag_gui, self.btn_demag_gui)

        text = "Thellier GUI"
        self.btn_thellier_gui = buttons.GenButton(self.panel, id=-1, label=text, size=(300, 50), name='thellier gui')
        self.btn_thellier_gui.SetBackgroundColour("#6ECFF6")
        self.btn_thellier_gui.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_run_thellier_gui, self.btn_thellier_gui)

        bSizer2.AddSpacer(20)
        bSizer2.Add(self.btn_demag_gui, 0, wx.ALIGN_CENTER, 0)
        bSizer2.AddSpacer(20)
        bSizer2.Add(self.btn_thellier_gui, 0, wx.ALIGN_CENTER, 0)
        bSizer2.AddSpacer(20)

        #---sizer 3 ----
        bSizer3 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Create file for upload to MagIC database"), wx.HORIZONTAL)

        text = "Create MagIC txt file for upload"
        self.btn_upload = buttons.GenButton(self.panel, id=-1, label=text, size=(300, 50))
        self.btn_upload.SetBackgroundColour("#C4DF9B")
        self.btn_upload.InitColours()

        bSizer3.AddSpacer(20)
        bSizer3.Add(self.btn_upload, 0, wx.ALIGN_CENTER, 0)
        bSizer3.AddSpacer(20)
        self.Bind(wx.EVT_BUTTON, self.on_btn_upload, self.btn_upload)


        #---arange sizers ----

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(5)
        #vbox.Add(self.logo,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(5)
        vbox.Add(bSizer0, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)
        #vbox.Add(bSizer0_1, 0, wx.ALIGN_CENTER, 0)
        #vbox.AddSpacer(10)
        vbox.Add(bSizer1, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)
        vbox.Add(bSizer2, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)
        vbox.Add(bSizer3, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)
        hbox.AddSpacer(10)
        hbox.Add(vbox, 0, wx.ALIGN_CENTER, 0)
        hbox.AddSpacer(5)

        self.panel.SetSizer(hbox)
        hbox.Fit(self)

    #----------------------------------------------------------------------

    def get_DIR(self):
        """
        Choose a working directory dialog
        """
        if "-WD" in sys.argv and self.FIRST_RUN:
            ind = sys.argv.index('-WD')
            self.WD = os.path.abspath(sys.argv[ind+1])
            os.chdir(self.WD)
            self.WD = os.getcwd()
            self.dir_path.SetValue(self.WD)
        else:
            self.on_change_dir_button(None)
            #self.WD = os.getcwd()

        self.FIRST_RUN = False
        # this functionality is not fully working yet, so I've removed it for now
        #try:
        #    print "trying listdir"
        #    os.listdir(self.WD)
        #except Exception as ex:
        #    print ex
        #print "self.WD.split('/')", self.WD.split('/')
        #if len(self.WD.split('/')) <= 4:
        #    print "no to saving this directory"
        #else:
        #    print "do on_save_dir_button"
        # self.on_save_dir_button(None)


    #----------------------------------------------------------------------

    #def getFolderBitmap():
    #    img = folder_icon.GetImage().Rescale(50, 50)
    #    return img.ConvertToBitmap()


    def on_change_dir_button(self, event, show=True):
        currentDirectory = os.getcwd()
        self.change_dir_dialog = wx.DirDialog(self.panel, "Choose your working directory to create or edit a MagIC contribution:", defaultPath=currentDirectory, style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if show:
            self.on_finish_change_dir(self.change_dir_dialog)

    def on_finish_change_dir(self, dialog, show=True):
        if not show:
            self.WD = dialog.GetPath()
            os.chdir(self.WD)
            self.dir_path.SetValue(self.WD)
        elif dialog.ShowModal() == wx.ID_OK:
            self.WD = dialog.GetPath()
            os.chdir(self.WD)
            self.dir_path.SetValue(self.WD)
            dialog.Destroy()
            if self.data_model_num == 2:
                self.get_wd_data2()
            else:
                self.get_wd_data()
        else:
            dialog.Destroy()


#    def on_revert_dir_button(self, event):
#        if self.last_saved_time.GetLineText(0) == "not saved":
#            dia = wx.MessageDialog(self.panel, "You can't revert, because your working directory has not been saved.  Are you sure you're in the right directory?", "Can't be done", wx.OK)
#            dia.ShowModal()
#            return
#        dia = wx.MessageDialog(self.panel, "Are you sure you want to revert to the last saved state?  All changes since {} will be lost".format(self.last_saved_time.GetLineText(0)), "Not so fast", wx.YES_NO|wx.NO_DEFAULT)
#        ok = dia.ShowModal()
#        if ok == wx.ID_YES:
#            os.chdir('..')
#            wd = self.WD
#            shutil.rmtree(wd)
#            shutil.move(self.saved_dir, self.WD)
#            os.chdir(self.WD)
#            self.on_save_dir_button(None)
#        else:
#            print "-I Don't revert"


#    def on_save_dir_button(self, event):
#        try:
#            if len(self.WD.split('/')) <= 4:
#                self.last_saved_time.Clear()
#                self.last_saved_time.write("not saved")
#                return
#            os.chdir('..')
#            wd = self.WD
#            wd = wd.rstrip('/')
#            ind = wd.rfind('/') + 1
#            saved_prefix, saved_folder = wd[:ind], wd[ind:]
#            self.saved_dir = saved_prefix + "copy_" + saved_folder
#            if "copy_" + saved_folder in os.listdir(saved_prefix):
#                shutil.rmtree(self.saved_dir)
#            shutil.copytree(self.WD, self.saved_dir)
#            self.last_saved_time.Clear()
#            now = datetime.datetime.now()
#            now_string = "{}:{}:{}".format(now.hour, now.minute, now.second)
#            self.last_saved_time.write(now_string)
#            os.chdir(self.WD)
#        except:# OSError:
#            print "-I Problem copying working directory"
#            self.last_saved_time.Clear()
#            self.last_saved_time.write("not saved")

    def on_run_thellier_gui(self, event):

        outstring = "thellier_gui.py -WD %s"%self.WD
        print("-I- running python script:\n %s"%(outstring))
        if self.data_model_num == 2.5:
            thellier_gui.main(self.WD, standalone_app=False, parent=self, DM=self.data_model_num)
        else:
            # disable and hide Pmag GUI mainframe
            self.Disable()
            self.Hide()
            # show busyinfo
            wait = wx.BusyInfo('Compiling required data, please wait...')
            wx.Yield()
            # create custom Thellier GUI closing event and bind it
            ThellierGuiExitEvent, EVT_THELLIER_GUI_EXIT = newevent.NewCommandEvent()
            self.Bind(EVT_THELLIER_GUI_EXIT, self.on_analysis_gui_exit)
            # make and show the Thellier GUI frame
            thellier_gui_frame = thellier_gui.Arai_GUI(self.WD, self,
                                                       standalone=False,
                                                       DM=self.data_model_num,
                                                       evt_quit=ThellierGuiExitEvent)
            if not thellier_gui_frame: print("Thellier GUI failed to start aborting"); del wait; return
            thellier_gui_frame.Centre()
            thellier_gui_frame.Show()
            del wait


    def on_run_demag_gui(self, event):
        outstring = "demag_gui.py -WD %s"%self.WD
        print("-I- running python script:\n %s"%(outstring))
        if self.data_model_num == 2:
            demag_gui.start(self.WD, standalone_app=False, parent=self, DM=self.data_model_num)
        else:
            # disable and hide Pmag GUI mainframe
            self.Disable()
            self.Hide()
            # show busyinfo
            wait = wx.BusyInfo('Compiling required data, please wait...')
            wx.Yield()
            # create custom Demag GUI closing event and bind it
            DemagGuiExitEvent, EVT_DEMAG_GUI_EXIT = newevent.NewCommandEvent()
            self.Bind(EVT_DEMAG_GUI_EXIT, self.on_analysis_gui_exit)
            # make and show the Demag GUI frame
            demag_gui_frame = demag_gui.Demag_GUI(self.WD, self,
                                                  write_to_log_file=False,
                                                  data_model=self.data_model_num,
                                                  evt_quit=DemagGuiExitEvent)
            demag_gui_frame.Centre()
            demag_gui_frame.Show()
            del wait


    def on_analysis_gui_exit(self, event):
        """
        When Thellier or Demag GUI closes,
        show and enable Pmag GUI main frame.
        Read in an updated contribution object
        based on any changed files.
        (For Pmag GUI 3.0 only)
        """
        self.Enable()
        self.Show()
        # also, refresh contribution object based on files
        # that may have been written/overwritten by Thellier GUI
        self.get_wd_data()


    def on_convert_file(self, event):
        pmag_dialogs_dia = pmag_basic_dialogs.import_magnetometer_data(self, wx.ID_ANY, '', self.WD)
        pmag_dialogs_dia.Show()
        pmag_dialogs_dia.Center()
        self.Hide()

    def on_convert_3(self, event):
        dia = pw.UpgradeDialog(None)
        dia.Center()
        res = dia.ShowModal()
        if res == wx.ID_CANCEL:
            webbrowser.open("https://www2.earthref.org/MagIC/upgrade", new=2)
            return
        ## more nicely styled way, but doesn't link to earthref
        #msg = "This tool is meant for relatively simple upgrades (for instance, a measurement file, a sample file, and a criteria file).\nIf you have a more complex contribution to upgrade, and you want maximum accuracy, use the upgrade tool at https://www2.earthref.org/MagIC/upgrade.\n\nDo you want to continue?"
        #result = pw.warning_with_override(msg)
        #if result == wx.ID_NO:
            #webbrowser.open("https://www2.earthref.org/MagIC/upgrade", new=2)
            #return
        # turn files from 2.5 --> 3.0 (rough translation)
        meas, upgraded, no_upgrade = pmag.convert_directory_2_to_3('magic_measurements.txt',
                                                                   input_dir=self.WD, output_dir=self.WD,
                                                                   data_model=self.contribution.data_model)
        if not meas:
            wx.MessageBox('2.5 --> 3.0 failed. Do you have a magic_measurements.txt file in your working directory?',
                          'Info', wx.OK | wx.ICON_INFORMATION)
            return

        # create a contribution
        self.contribution = nb.Contribution(self.WD)
        # make skeleton files with specimen, sample, site, location data
        self.contribution.propagate_measurement_info()
        #
        # note what DIDN'T upgrade
        #no_upgrade = []
        #for fname in os.listdir(self.WD):
        #    if 'rmag' in fname:
        #        no_upgrade.append(fname)
        #    elif fname in ['pmag_results.txt', 'pmag_criteria.txt',
        #                   'er_synthetics.txt', 'er_images.txt',
        #                   'er_plots.txt', 'er_ages.txt']:
        #        no_upgrade.append(fname)

        # pop up
        upgraded_string = ", ".join(upgraded)
        if no_upgrade:
            no_upgrade_string = ", ".join(no_upgrade)
            msg = '2.5 --> 3.0 translation completed!\n\nThese 3.0 format files were created: {}.\n\nHowever, these 2.5 format files could not be upgraded: {}.\n\nTo convert all 2.5 files, use the MagIC upgrade tool: https://www2.earthref.org/MagIC/upgrade\n'.format(upgraded_string, no_upgrade_string)
            if 'criteria.txt' in upgraded:
                msg += '\nNote: Please check your criteria file for completeness and accuracy, as not all 2.5 files will be fully upgraded.'
            if 'pmag_criteria.txt' in no_upgrade:
                msg += '\nNote: Not all criteria files can be upgraded, even on the MagIC site.  You may need to recreate an old pmag_criteria file from scratch in Thellier GUI or Demag GUI.'
            wx.MessageBox(msg, 'Warning', wx.OK | wx.ICON_INFORMATION)
        else:
            msg = '2.5 --> 3.0 translation completed!\nThese files were converted: {}'.format(upgraded_string)
            wx.MessageBox(msg, 'Info', wx.OK | wx.ICON_INFORMATION)



    def on_er_data(self, event):
        if self.data_model_num == 2:
            if not os.path.isfile(os.path.join(self.WD, 'magic_measurements.txt')):
                print('-W- {} is missing'.format(os.path.join(self.WD, 'magic_measurements.txt')))
                pw.simple_warning("Your working directory must have a magic_measurements.txt file to run this step.  Make sure you have fully completed step 1 (import magnetometer file), by combining all imported magnetometer files into one magic_measurements file.")
                return False

            #self.ErMagic_frame = ErMagicBuilder.MagIC_model_builder(self.WD, self, self.ErMagic_data)#,self.Data,self.Data_hierarchy)
            wait = wx.BusyInfo('Compiling required data, please wait...')
            wx.Yield()
            self.ErMagic_frame = ErMagicBuilder.MagIC_model_builder(self.WD, self, self.er_magic)#,self.Data,self.Data_hierarchy)
        elif self.data_model_num == 3:
            if not os.path.isfile(os.path.join(self.WD, 'measurements.txt')):
                pw.simple_warning("Your working directory must have a 3.0. format measurements.txt file to run this step.  Make sure you have fully completed step 1 (import magnetometer file) and ALSO converted to 3.0., if necessary), then try again.")
                return False

            wait = wx.BusyInfo('Compiling required data, please wait...')
            wx.Yield()
            self.ErMagic_frame = ErMagicBuilder.MagIC_model_builder3(self.WD, self, self.contribution)

        self.ErMagic_frame.Show()
        self.ErMagic_frame.Center()

        size = wx.DisplaySize()
        size = (size[0] - 0.3 * size[0], size[1] - 0.3 * size[1]) # gets total available screen space - 10%
        self.ErMagic_frame.Raise()
        del wait

    def init_check_window(self):
        self.check_dia = pmag_er_magic_dialogs.ErMagicCheckFrame(self, 'Check Data', self.WD, self.er_magic)# initiates the object that will control steps 1-6 of checking headers, filling in cell values, etc.

    def init_check_window3(self):
        self.check_dia = pmag_er_magic_dialogs.ErMagicCheckFrame3(self, 'Check Data', self.WD, self.contribution)


    def on_orientation_button(self, event):
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.Yield()
        #dw, dh = wx.DisplaySize()
        size = wx.DisplaySize()
        size = (size[0]-0.1 * size[0], size[1]-0.1 * size[1])
        if self.data_model_num == 3:
            frame = pmag_basic_dialogs.OrientFrameGrid3(self, -1, 'demag_orient.txt',
                                                        self.WD, self.contribution,
                                                        size)
        else:
            frame = pmag_basic_dialogs.OrientFrameGrid(self, -1, 'demag_orient.txt',
                                                        self.WD, self.er_magic, size)
        frame.Show(True)
        frame.Centre()
        self.Hide()
        del wait

    def on_unpack(self, event):
        dlg = wx.FileDialog(
            None, message = "choose txt file to unpack",
            defaultDir=self.WD,
            defaultFile="",
            style=wx.FD_OPEN #| wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
            input_dir, f = os.path.split(FILE)
        else:
            return False

        outstring="download_magic.py -f {} -WD {} -ID {}".format(f, self.WD, input_dir)

        # run as module:
        print("-I- running python script:\n %s"%(outstring))
        wait = wx.BusyInfo("Please wait, working...")
        wx.Yield()
        ex = None
        try:
            if ipmag.download_magic(f, self.WD, input_dir, overwrite=True):
                text = "Successfully ran download_magic.py program.\nMagIC files were saved in your working directory.\nSee Terminal/message window for details."
            else:
                text = "Something went wrong.  Make sure you chose a valid file downloaded from the MagIC database and try again."

        except Exception as ex:
            text = "Something went wrong.  Make sure you chose a valid file downloaded from the MagIC database and try again."
            del wait
            dlg = wx.MessageDialog(self, caption="Saved", message=text, style=wx.OK)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                dlg.Destroy()
            if ex:
                raise(ex)


    def on_btn_upload(self, event):
        outstring="upload_magic.py"
        print("-I- running python script:\n %s"%(outstring))
        wait = wx.BusyInfo("Please wait, working...")
        wx.Yield()
        if self.data_model_num == 3:
            res, error_message, has_problems, all_failing_items = ipmag.upload_magic3(dir_path=self.WD,
                                                                                      vocab=self.contribution.vocab,
                                                                                      contribution=self.contribution)
        if self.data_model_num == 2:
            res, error_message, errors = ipmag.upload_magic(dir_path=self.WD, data_model=self.er_magic.data_model)
            del wait

        if res:
            text = "You are ready to upload.\n Your file: {}  was generated in MagIC Project Directory.\nDrag and drop this file in the MagIC database.".format(os.path.split(res)[1])
            dlg = wx.MessageDialog(self, caption="Saved", message=text, style=wx.OK)
        else:
            text = "There were some problems with the creation of your upload file.\nError message: {}\nSee Terminal/message window for details".format(error_message)
            dlg = wx.MessageDialog(self, caption="Error", message=text, style=wx.OK)

        result = dlg.ShowModal()
        if result == wx.ID_OK:
            dlg.Destroy()

        if self.data_model_num == 3:
            from programs import magic_gui
            self.Disable()
            self.Hide()
            self.magic_gui_frame = magic_gui.MainFrame(self.WD,
                                                       dmodel=self.data_model,
                                                       title="Validations",
                                                       contribution=self.contribution)


            self.magic_gui_frame.validation_mode = ['specimens']
            self.magic_gui_frame.failing_items = all_failing_items
            self.magic_gui_frame.change_dir_button.Disable()
            self.magic_gui_frame.Centre()
            self.magic_gui_frame.Show()
            self.magic_gui_frame.highlight_problems(has_problems)
            #
            # change name of upload button to 'exit validation mode'
            self.magic_gui_frame.bSizer2.GetStaticBox().SetLabel('return to main GUI')
            self.magic_gui_frame.btn_upload.SetLabel("exit validation mode")
            # bind that button to quitting magic gui and re-enabling Pmag GUI
            self.magic_gui_frame.Bind(wx.EVT_BUTTON, self.on_end_validation, self.magic_gui_frame.btn_upload)

    def on_end_validation(self, event):
        self.Enable()
        self.Show()
        self.magic_gui_frame.Destroy()



    def on_menu_exit(self, event):
        # also delete appropriate copy file
        try:
            self.help_window.Destroy()
        except:
            pass
        if '-i' in sys.argv:
            self.Destroy()
        try:
            sys.exit() # can raise TypeError if wx inspector was used
        except Exception as ex:
            if isinstance(ex, TypeError):
                pass
            else:
                raise ex

def main():
    if '-h' in sys.argv:
        help_msg = """
Runs Pmag GUI for uploading, downloading, analyzing and visualizing
data.

SYNTAX
    pmag_gui.py [command line options]
    # or, for Anaconda users:
    pmag_gui_anaconda [command line options]

INFORMATION
    See https://earthref.org/PmagPy/cookbook/#pmag_gui.py for a complete tutorial
"""
        print(help_msg)
        sys.exit()
    print('-I- Starting Pmag GUI - please be patient')
    # if redirect is true, wxpython makes its own output window for stdout/stderr
    if 'darwin' in sys.platform:
        app = wx.App(redirect=False)
    else:
        app = wx.App(redirect=True)
    app.frame = MagMainFrame()
    working_dir = pmag.get_named_arg_from_sys('-WD', '.')
    app.frame.Show()
    app.frame.Center()
    ## use for debugging:
    #if '-i' in sys.argv:
    #    import wx.lib.inspection
    #    wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

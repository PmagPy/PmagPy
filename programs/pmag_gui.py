#!/usr/bin/env pythonw

# pylint: disable=W0612,C0111,C0103,W0201

print "-I- Importing Pmag GUI dependencies"
#from pmag_env import set_env
#set_env.set_backend(wx=True)
import matplotlib
if not matplotlib.get_backend() == 'WXAgg':
    matplotlib.use('WXAgg')
import wx
import wx.lib.buttons as buttons
#import thellier_gui_dialogs
import os
import sys
#import datetime
#import shutil
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
import pmagpy.builder as builder
import dialogs.pmag_basic_dialogs as pmag_basic_dialogs
import dialogs.pmag_er_magic_dialogs as pmag_er_magic_dialogs
import dialogs.pmag_gui_menu as pmag_gui_menu
import dialogs.ErMagicBuilder as ErMagicBuilder
from programs import demag_gui
from programs import thellier_gui

# import check_updates

class MagMainFrame(wx.Frame):
    """"""
    try:
        version= pmag.get_version()
    except:
        version = ""
    title = "Pmag GUI   version: %s"%version
    if sys.platform in ['win32', 'win64']:
        title += "   Powered by Enthought Canopy"

    def __init__(self, WD=None):

        self.FIRST_RUN = True
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title, name='pmag_gui mainframe')
        self.panel = wx.Panel(self, name='pmag_gui main panel')
        self.InitUI()

        # for use as module:
        self.resource_dir = os.getcwd()

        if not WD:
            self.get_DIR()        # choose directory dialog
        else:
            self.WD = WD
        self.HtmlIsOpen = False
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)
        self.er_magic = builder.ErMagicBuilder(self.WD)
        #self.er_magic.init_default_headers()
        #self.er_magic.init_actual_headers()


    def InitUI(self):

        menubar = pmag_gui_menu.MagICMenu(self)
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
        self.change_dir_button = buttons.GenButton(self.panel, id=-1, label="change dir",size=(-1, -1))
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

        TEXT="1. convert magnetometer files to MagIC format"
        self.btn1 = buttons.GenButton(self.panel, id=-1, label=TEXT, size=(450, 50), name='step 1')
        self.btn1.SetBackgroundColour("#FDC68A")
        self.btn1.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_convert_file, self.btn1)
        text = "2. (optional) calculate geographic/tilt-corrected directions"
        self.btn2 = buttons.GenButton(self.panel, id=-1, label=text, size=(450, 50), name='step 2')
        self.btn2.SetBackgroundColour("#FDC68A")
        self.btn2.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_orientation_button, self.btn2)
        text = "3. complete EarthRef data using EarthRef MagIC Builder "
        self.btn3 = buttons.GenButton(self.panel, id=-1, label=text, size=(450, 50), name='step 3')
        self.btn3.SetBackgroundColour("#FDC68A")
        self.btn3.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_er_data, self.btn3)

        text = "unpack txt file downloaded from MagIC"
        self.btn4 = buttons.GenButton(self.panel, id=-1, label=text, size=(300, 50))
        self.btn4.SetBackgroundColour("#FDC68A")
        self.btn4.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_unpack, self.btn4)

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
        bSizer1.Add(self.btn4, 0, wx.ALIGN_CENTER, 0)
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
        bSizer3 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Upload to MagIC database"), wx.HORIZONTAL)

        text = "prepare txt file for upload"
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

        else:
            self.WD = os.getcwd()

        os.chdir(self.WD)
        self.WD = os.getcwd()
        self.dir_path.SetValue(self.WD)
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
            #self.ErMagic_data = ErMagicBuilder.ErMagicBuilder(self.WD)
            self.er_magic = builder.ErMagicBuilder(self.WD, self.er_magic.data_model)
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
        print "-I- running python script:\n %s"%(outstring)
        thellier_gui.main(self.WD, standalone_app=False, parent=self)

    def on_run_demag_gui(self, event):
        outstring = "demag_gui.py -WD %s"%self.WD
        print "-I- running python script:\n %s"%(outstring)
        demag_gui.main(self.WD, standalone_app=False, parent=self)

    def on_convert_file(self, event):
        pmag_dialogs_dia = pmag_basic_dialogs.import_magnetometer_data(self, wx.ID_ANY, '', self.WD)
        pmag_dialogs_dia.Show()
        pmag_dialogs_dia.Center()
        self.Hide()

    def on_er_data(self, event):
        if not os.path.isfile(os.path.join(self.WD, 'magic_measurements.txt')):
            import dialogs.pmag_widgets as pw
            pw.simple_warning("Your working directory must have a magic_measurements.txt file to run this step.  Make sure you have fully completed step 1 (import magnetometer file), by combining all imported magnetometer files into one magic_measurements file.")
            return False

        #self.ErMagic_frame = ErMagicBuilder.MagIC_model_builder(self.WD, self, self.ErMagic_data)#,self.Data,self.Data_hierarchy)
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.Yield()
        self.ErMagic_frame = ErMagicBuilder.MagIC_model_builder(self.WD, self, self.er_magic)#,self.Data,self.Data_hierarchy)
        self.ErMagic_frame.Show()
        self.ErMagic_frame.Center()

        size = wx.DisplaySize()
        size = (size[0] - 0.3 * size[0], size[1] - 0.3 * size[1]) # gets total available screen space - 10%
        self.ErMagic_frame.Raise()
        del wait

    def init_check_window(self):
        self.check_dia = pmag_er_magic_dialogs.ErMagicCheckFrame(self, 'Check Data', self.WD, self.er_magic)# initiates the object that will control steps 1-6 of checking headers, filling in cell values, etc.

    def on_orientation_button(self, event):
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.Yield()
        #dw, dh = wx.DisplaySize()
        size = wx.DisplaySize()
        size = (size[0]-0.1 * size[0], size[1]-0.1 * size[1])
        frame = pmag_basic_dialogs.OrientFrameGrid(self, -1, 'demag_orient.txt', self.WD, self.er_magic, size)
        frame.Show(True)
        frame.Centre()
        self.Hide()
        del wait

    def on_unpack(self, event):
        dlg = wx.FileDialog(
            None, message = "choose txt file to unpack",
            defaultDir=self.WD,
            defaultFile="",
            style=wx.OPEN #| wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
            input_dir, f = os.path.split(FILE)
        else:
            return False

        outstring="download_magic.py -f {} -WD {} -ID {}".format(f, self.WD, input_dir)

        # run as module:
        print "-I- running python script:\n %s"%(outstring)
        wait = wx.BusyInfo("Please wait, working...")
        wx.Yield()
        ex = None
        try:
            if ipmag.download_magic(f, self.WD, input_dir, overwrite=True):
                text = "Successfully ran download_magic.py program.\nMagIC files were saved in your working directory.\nSee Terminal/Command Prompt for details."
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
        print "-I- running python script:\n %s"%(outstring)
        wait = wx.BusyInfo("Please wait, working...")
        wx.Yield()

        upfile, error_message, errors = ipmag.upload_magic(dir_path=self.WD, data_model=self.er_magic.data_model)
        del wait
        if upfile:
            text = "You are ready to upload.\n Your file: {}  was generated in MagIC Project Directory.\nDrag and drop this file in the MagIC database.".format(os.path.split(upfile)[1])
            dlg = wx.MessageDialog(self, caption="Saved", message=text, style=wx.OK)
        else:
            text = "There were some problems with the creation of your upload file.\nError message: {}\nSee Terminal/Command Prompt for details".format(error_message)
            dlg = wx.MessageDialog(self, caption="Error", message=text, style=wx.OK)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            dlg.Destroy()


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
        print "See https://earthref.org/PmagPy/cookbook/#pmag_gui.py for a complete tutorial"
        sys.exit()
    print '-I- Starting Pmag GUI - please be patient'
    # if redirect is true, wxpython makes its own output window for stdout/stderr
    app = wx.App(redirect=False)
    app.frame = MagMainFrame()
    working_dir = pmag.get_named_arg_from_sys('-WD', '.')

    ## this causes an error with Canopy Python
    ## (it works with brew Python)
    ## need to use these lines for Py2app
    #if working_dir == '.':
    #    app.frame.on_change_dir_button(None)

    app.frame.Show()
    app.frame.Center()
    ## use for debugging:
    #if '-i' in sys.argv:
    #    import wx.lib.inspection
    #    wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
            

if __name__ == "__main__":
    main()

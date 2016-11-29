#!/usr/bin/env python

import unittest
import wx,os,shutil
#import SPD
#import wx.lib.inspection
#import numpy as np
#import ipmag
#import pmag_gui
#import pmag_menu_dialogs
from programs import thellier_gui
import dialogs.thellier_interpreter as thellier_interpreter

class TestThellierGUI(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = thellier_gui.Arai_GUI(project_WD,test_mode=True)
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        self.app.Destroy()
        os.chdir(WD)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertTrue(self.pnl.IsShown())

    def test_auto_interpreter(self):
        menu = self.get_menu_from_frame(self.frame,'Auto Interpreter')
        item_id = menu.FindItem('&Run Thellier auto interpreter')
        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], item_id)
        self.frame.ProcessEvent(event)

    def test_interpreter(self):
        THERMAL = True
        MICROWAVE = False
        interpreter = thellier_interpreter.thellier_auto_interpreter(self.frame.Data, self.frame.Data_hierarchy, self.frame.WD, self.frame.acceptance_criteria, self.frame.preferences, self.frame.GUI_log, THERMAL, MICROWAVE)
        program_ran, num_specs = interpreter.run_interpreter()
        self.assertTrue(program_ran)
        self.assertEqual(5, num_specs)

    def get_menu_from_frame(self,frame,menu_name):
        mb = frame.GetMenuBar()
        for m, n in mb.Menus:
            if n == menu_name: return m

def backup(WD):
    print("backing up")
    #make backup directory
    backup_dir = os.path.join(WD,'.backup')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    #copy test files to backup
    src_files = os.listdir(WD)
    for file_name in src_files:
        full_file_name = os.path.join(WD, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, os.path.join(backup_dir,file_name))

def revert_from_backup(WD):
    print("reverting")
    backup_dir = os.path.join(WD,'.backup')
    #copy test files to backup
    src_files = os.listdir(backup_dir)
    for file_name in src_files:
        full_file_name = os.path.join(backup_dir, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, os.path.join(WD,file_name))
            os.remove(full_file_name)
    if os.path.exists(backup_dir):
        os.rmdir(backup_dir)

if __name__ == '__main__':
    # set constants
    WD = os.getcwd()
    project_WD = os.path.join(WD, 'data_files', 'testing', 'my_project')

    backup(project_WD)
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestThellierGUI))
    revert_from_backup(project_WD)

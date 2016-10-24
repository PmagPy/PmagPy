#!/usr/bin/env python

import unittest
import os
import wx
#import SPD
#import wx.lib.inspection
#import numpy as np
#import ipmag
#import pmag_gui
#import pmag_menu_dialogs
from programs import thellier_gui
import dialogs.thellier_interpreter as thellier_interpreter

# set constants
WD = os.getcwd()
PROJECT_WD = os.path.join(WD, 'data_files', 'testing', 'my_project')


class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = thellier_gui.Arai_GUI(PROJECT_WD)
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

    @unittest.skip('calls a ShowModal(), so is inconvenient')
    def test_auto_interpreter(self):
        menus = self.frame.MenuBar.Menus
        for m, name in menus:
            if name == '&Auto Interpreter':
                menu = m
                break
        item_id = menu.FindItem('&Run Thellier auto interpreter')
        #item = menu.FindItemById(item_id)

        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], item_id)
        self.frame.GetEventHandler().ProcessEvent(event)

    def test_interpreter(self):
        THERMAL = True
        MICROWAVE = False
        interpreter = thellier_interpreter.thellier_auto_interpreter(self.frame.Data,
                                                                     self.frame.Data_hierarchy,
                                                                     self.frame.WD,
                                                                     self.frame.acceptance_criteria,
                                                                     self.frame.preferences,
                                                                     self.frame.GUI_log,
                                                                     THERMAL, MICROWAVE)
        program_ran, num_specs = interpreter.run_interpreter()
        self.assertTrue(program_ran)
        self.assertEqual(5, num_specs)


if __name__ == '__main__':
    unittest.main()

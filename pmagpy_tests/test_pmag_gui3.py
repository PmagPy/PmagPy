#!/usr/bin/env python

import pmagpy
import unittest
import os
import sys
import wx
#import wx.lib.inspection
import programs.pmag_gui3 as pmag_gui
from pmagpy import new_builder as nb
#import dialogs.pmag_menu_dialogs as pmag_menu_dialogs

# get WD before all the Pmag GUI stuff starts to happen
WD = sys.prefix
project_WD = os.path.join(WD, "pmagpy_data_files", "Pmag_GUI", "3_0")
test_dir = os.getcwd()

class TestMainFrame(unittest.TestCase):

    def setUp(self):
        os.chdir(test_dir)
        self.app = wx.App()
        self.frame = pmag_gui.MagMainFrame(project_WD, DM=3)
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        return

    def test_data_object_is_created(self):
        self.assertEqual(nb.Contribution, type(self.frame.contribution))
        self.assertIn('measurements', self.frame.contribution.tables)
        self.assertIn('specimens', self.frame.contribution.tables)
        self.assertIn('samples', self.frame.contribution.tables)
        self.assertEqual('hz05a1', self.frame.contribution.tables['specimens'].df.index[1])

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertTrue(self.pnl.IsShown())
        self.assertEqual('pmag_gui main panel', self.pnl.GetName())

    def test_click_button_one(self):
        """
        make sure import window is created when user clicks btn 1
        """
        window = self.does_top_window_exist(self.pnl, 'step 1', 'import_magnetometer_data')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_click_button_one_a(self):
        child_names = [child.GetName() for child in self.pnl.GetChildren()]
        self.assertIn('step 1a', child_names)

    def test_click_button_two(self):
        """
        make sure orientation_magic window is created when user clicks btn 2
        """
        window = self.does_top_window_exist(self.pnl, 'step 2', 'calculate geographic directions')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_click_button_three(self):
        """
        make sure ErMagicBuilder window is created when user clicks btn 3
        """
        window = self.does_top_window_exist(self.pnl, 'step 3', 'ErMagicBuilder')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_click_demag_gui(self):
        """
        make sure demag_gui window is created when users clicks btn
        """
        window = self.does_top_window_exist(self.pnl, 'demag gui', 'demag gui')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_thellier_gui(self):
        """
        make sure thellier_gui window is created when users clicks btn
        """

        window = self.does_top_window_exist(self.pnl, 'thellier gui', 'thellier gui')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())



    def does_top_window_exist(self, parent, btn_name, window_name):
        """
        produces a click event on the button called btn_name,
        see if it produces a top-level window called window_name
        """
        btn = None
        children = parent.GetChildren()
        #print ", ".join([child.GetName() for child in children])
        for child in children:
            if child.GetName() == btn_name:
                btn = child
                break
        if not btn:
            return None
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        btn.GetEventHandler().ProcessEvent(event)
        for wind in wx.GetTopLevelWindows():
            if wind.GetName() == window_name:
                return wind
        return None

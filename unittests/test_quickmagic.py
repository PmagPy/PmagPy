#!/usr/bin/env python

import unittest
import sys
import os
import wx
import numpy as np
import ipmag
import QuickMagIC as qm






class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        self.frame = qm.MagMainFrame()
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled)
        self.assertEqual('quickmagic main panel', self.pnl.GetName())

    def test_click_button_one(self):
        """
        make sure import window is created when user clicks btn 1
        """
        window = self.does_window_exist('step 1', 'import_magnetometer_data')
        self.assertTrue(window)

    def test_click_button_two(self):
        """
        make sure orientation_magic window is created when user clicks btn 2
        """
        window = self.does_window_exist('step 2', 'calculate geographic directions')
        self.assertTrue(window)

    def test_click_button_three(self):
        """
        make sure ErMagicBuilder window is created when user clicks btn 3
        """
        window = self.does_window_exist('step 3', 'ErMagicBuilder')
        self.assertTrue(window)

    def test_click_demag_gui(self):
        """
        make sure demag_gui window is created when users clicks btn
        """
        window = self.does_window_exist('demag gui', 'demag gui')
        self.assertTrue(window)

    def test_click_thellier_gui(self):
        """
        make sure thellier_gui window is created when users clicks btn
        """
        window = self.does_window_exist('thellier gui', 'thellier gui')
        self.assertTrue(window)


    def test_click_download_magic(self):
        pass

    def test_click_upload_magic(self):
        pass

    def test_click_change_dir(self):
        btn = self.frame.change_dir_button
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        print 'event', event
        #btn.GetEventHandler().ProcessEvent(event)
        
        # the problem is that this creates a modal event..
        
    
    def does_window_exist(self, btn_name, window_name):
        btn, window = None, None
        pnl_children = self.pnl.GetChildren()
        for child in pnl_children:
            if child.GetName() == btn_name:
                btn = child
                break
        if not btn:
            return None
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        btn.GetEventHandler().ProcessEvent(event)
        frame_children = self.frame.GetChildren()
        for child in frame_children:
            if child.GetName() == window_name:
                window = child
                break
        if not window:
            return None
        else:
            return window



if __name__ == '__main__':
    unittest.main()
            

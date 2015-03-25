#!/usr/bin/env python

import unittest
import sys
import os
import wx
import numpy as np
import ipmag
import QuickMagIC as qm

class TestBasic(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        self.frame = qm.MagMainFrame()
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        self.frame.Destroy()

    def test_fake(self):
        self.assertEqual(1, 1)

    def test_next(self):
        self.assertFalse(False)

    def test_main_panel_is_created(self):
        self.assertTrue(self.pnl.IsEnabled)
        self.assertEqual('quickmagic main panel', self.pnl.GetName())

    def test_click_import_button(self):
        children = self.pnl.GetChildren()
        print 'types of children'
        for child in children:
            print 'type:', type(child)
            print 'name:', child.GetName()
            if child.GetName() == 'step 1':
                import_btn = child
                break
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, import_btn.GetId())
        import_btn.GetEventHandler().ProcessEvent(event)
        # make sure the proper window gets created
            




if __name__ == '__main__':
    unittest.main()
            

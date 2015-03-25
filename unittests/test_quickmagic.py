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

    def tearDown(self):
        self.frame.Destroy()

    def test_fake(self):
        self.assertEqual(1, 1)

    def test_next(self):
        self.assertFalse(False)

    def test_main_panel_is_created(self):
        pnl = self.frame.GetChildren()[0]
        children = pnl.GetChildren()
        print 'types of children'
        for child in children:
            print type(child)
        self.assertTrue(pnl.IsEnabled)
        self.assertEqual('quickmagic main panel', pnl.GetName())

    def test_click_import_button(self):
        pass



if __name__ == '__main__':
    unittest.main()
            

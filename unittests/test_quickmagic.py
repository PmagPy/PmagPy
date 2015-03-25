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

    def test_event(self):
        print 'self.frame:', self.frame
        pnl = self.frame.GetChildren()[0]
        print 'pnl.GetName', pnl.GetName()
        print 'pnl.IsEnabled', pnl.IsEnabled()
        print 'pnl.GetId', pnl.GetId()
        children = pnl.GetChildren()
        print 'types of children'
        for child in children:
            print type(child)
        self.assertTrue(pnl.IsEnabled)



if __name__ == '__main__':
    unittest.main()
            

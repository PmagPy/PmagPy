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
        print self.frame
        self.assertEqual(1, 1)

    def test_next(self):
        self.assertFalse(False)

    def test_event(self):
        for each in self.frame.GetChildren():
            for child in each.GetChildren():
                print 'child', child



if __name__ == '__main__':
    unittest.main()
            

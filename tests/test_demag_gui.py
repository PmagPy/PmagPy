#!/usr/bin/env python

import unittest
import os
import wx
import sys
import wx.lib.inspection
from programs import demag_gui

WD = sys.prefix
project_WD = os.path.join(WD, 'pmag_data_files', 'testing', 'my_project')
core_depthplot_WD = os.path.join(WD, 'pmag_data_files', 'core_depthplot')

class TestMainFrame(unittest.TestCase):
    def setUp(self):
        self.app = wx.App()
        self.frame = demag_gui.Zeq_GUI(project_WD)

    def tearDown(self):
        self.app.Destroy()
        os.chdir(WD)

if __name__ == '__main__':
    unittest.main()


#!/usr/bin/env python

import unittest
import os
import wx
import wx.lib.inspection
from programs import demag_gui

WD = os.getcwd()
project_WD = os.path.join(os.getcwd(), 'tests', 'examples', 'my_project')
core_depthplot_WD = os.path.join(os.getcwd(), 'data_files', 'core_depthplot')

class TestMainFrame(unittest.TestCase):
    def setUp(self):
        self.app = wx.App()
        self.frame = demag_gui.Zeq_GUI(project_WD)

    def tearDown(self):
        self.app.Destroy()
        os.chdir(WD)

if __name__ == '__main__':
    unittest.main()


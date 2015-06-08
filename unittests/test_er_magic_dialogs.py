#!/usr/bin/env python

import unittest
#import sys
import os
import wx
import make_magic
import pmag_er_magic_dialogs

#import wx.lib.inspection
#import numpy as np
#import ipmag
#import QuickMagIC as qm

WD = os.getcwd()
project_WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')

class TestMagicGrid(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        self.frame = wx.Frame(None, wx.ID_ANY, 'Title', size=(600, 600))
        self.frame.pnl = wx.Panel(self.frame, name='a panel')

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_add_col(self):
        row_labels = ['alpha', 'bravo', 'charlie', 'whiskey', 'x-ray', 'y', 'z']
        col_labels = ['delta', 'echo', 'foxtrot', 'gamma']
        grid = pmag_er_magic_dialogs.MagicGrid(self.frame.pnl, 'grid', row_labels, col_labels, size=(600, 600))
        grid.InitUI()
        grid.size_grid()

        label = 'new_label'
        grid.add_col(label)
        cols = grid.GetNumberCols()

        self.assertEqual(label, str(grid.GetColLabelValue(cols-1)))


class TestMakeMagicMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = make_magic.MainFrame(project_WD, "my panel")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertEqual("my panel", str(self.pnl.GetName()))

    def test_grid_is_created(self):
        """
        """
        self.assertTrue(self.frame.grid)



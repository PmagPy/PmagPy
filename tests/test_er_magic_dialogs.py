#!/usr/bin/env python

import unittest
import sys
import os
import wx

import dialogs.magic_grid as magic_grid

#import wx.lib.inspection
#import numpy as np
#import ipmag

WD = sys.prefix
project_WD = os.path.join(WD, 'pmagpy_data_files', 'testing', 'my_project')

class TestMagicGrid(unittest.TestCase):
    """
    testing for MagicGrid class
    """

    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None, wx.ID_ANY, 'Title', size=(600, 600))
        self.frame.pnl = wx.Panel(self.frame, name='a panel')
        row_labels = ['alpha', 'bravo', 'charlie', 'whiskey', 'x-ray', 'y', 'z']
        col_labels = ['delta', 'echo', 'foxtrot', 'gamma']
        self.grid = magic_grid.MagicGrid(self.frame.pnl, 'grid', row_labels, col_labels, size=(600, 600))
        self.grid.InitUI()
        self.grid.size_grid()

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_add_row(self):
        label = 'new_label'
        self.grid.add_row(label)
        last_row = self.grid.GetNumberRows() - 1
        self.assertEqual(label, str(self.grid.GetCellValue(last_row, 0)))

    def test_add_row_no_label(self):
        self.grid.add_row()
        last_row = self.grid.GetNumberRows() - 1
        self.assertEqual('', self.grid.GetCellValue(last_row, 0))
        self.assertEqual('', self.grid.row_labels[-1])

    def test_remove_row(self):
        num_rows = self.grid.GetNumberRows()
        last_row_name = self.grid.GetCellValue(num_rows - 1, 0)
        self.grid.remove_row()
        self.assertEqual(num_rows - 1, self.grid.GetNumberRows())
        new_num_rows = self.grid.GetNumberRows()
        new_last_row_name = self.grid.GetCellValue(new_num_rows - 1, 0)
        self.assertNotEqual(new_num_rows, num_rows)
        self.assertNotEqual(new_last_row_name, last_row_name)
        self.assertEqual('y', self.grid.row_labels[-1])

    def test_remove_row_charlie(self):
        old_row_name = self.grid.GetCellValue(2, 0)
        self.assertEqual('charlie', old_row_name)
        self.grid.remove_row(2)
        self.assertEqual('whiskey', self.grid.GetCellValue(2, 0))
        self.assertEqual('whiskey', self.grid.row_labels[2])

    @unittest.skip('this just hangs')
    def test_add_col(self):
        label = 'new_label'
        self.grid.add_col(label)
        cols = self.grid.GetNumberCols()
        self.assertEqual(label, str(self.grid.GetColLabelValue(cols-1)))
        self.assertEqual(label, self.grid.col_labels[-1])

    @unittest.skipIf(sys.platform != 'darwin', 'fails remotely for unknown reason')
    def test_remove_col(self):
        self.grid.add_col('victor')
        num_cols = self.grid.GetNumberCols()
        result = self.grid.remove_col(2)
        new_num_cols = self.grid.GetNumberCols()
        self.assertNotEqual(num_cols, new_num_cols)
        # remove foxtrot, gamma should be in position 2
        self.assertEqual('gamma', self.grid.GetColLabelValue(2))
        self.assertEqual('gamma', self.grid.col_labels[2])
        self.assertNotIn('foxtrot', self.grid.col_labels)

    def test_changes_after_row_delete(self):
        self.grid.changes = {1, 3, 6}
        self.grid.remove_row(3)
        correct_changes = {-1, 1, 5}
        self.assertEqual(correct_changes, self.grid.changes)

    def test_changes_after_multiple_row_delete(self):
        self.grid.changes = {1, 2, 3, 6}
        self.grid.remove_row(2)
        self.grid.remove_row(3)
        correct_changes = {-1, 1, 2, 4}
        self.assertEqual(correct_changes, self.grid.changes)



#!/usr/bin/env python

import wx
import unittest


class MyDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'Test')
        self.btn = wx.Button(self, btn_id, label="OK!!")
        self.btn.Bind(wx.EVT_BUTTON, self.close_dialog)

    def close_dialog(self, event):
        self.Parent.Destroy()


class MyPanel(wx.Panel):
    def __init__(self, parent):
        print 'initing MyPanel'
        wx.Panel.__init__(self, parent, -1)
        print 'halfway through initing MyPanel'
        #self.btn = wx.Button(self, btn_id, label="OK!!")
        print 'finished initing MyPanel'


class TestMyDialog(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.frame.Show()
        print 'self.app set up', self.app

    def tearDown(self):
        self.app.Destroy()

    def test_true(self):
        self.assertTrue(True)

    def test_fake(self):
        print wx.__version__
        enabled = self.ShowPanel()
        print 'enabled?', enabled
        self.assertTrue(enabled)
        print 'done test'

    def ShowPanel(self):
        print 'doing ShowPanel'
        self.pnl = MyPanel(self.frame)
        print 'made pnl'
        self.pnl.Show()
        print 'showed pnl'
        enabled = self.pnl.IsEnabled()
        print 'pnl is enabled?', enabled
        self.pnl.Destroy()
        print 'done ShowPanel'
        return enabled



if __name__ == '__main__':
    unittest.main()

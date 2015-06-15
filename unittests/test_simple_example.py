#!/usr/bin/env python

import wx
#import unittest

btn_id = wx.NewId()


ignore = """
class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        #self.btn = wx.Button(self, btn_id, label="OK!!")

        
class MyDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'Dialogo')
        self.btn = wx.Button(self, btn_id, label="OK!!")
        self.btn.Bind(wx.EVT_BUTTON, self.close_dialog)

    def close_dialog(self, event):
        self.EndModal(wx.ID_OK)
        self.Parent.Destroy()


class TestMyDialog(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)
        #self.frame.Show()

    def tearDown(self):
        self.app.Destroy()

    def test_true(self):
        self.assertTrue(True)

    def test_dia(self):
        pass
        #result = self.ShowDia()
        #self.assertEqual(result, wx.ID_OK)

    def ShowDia(self):
        #self.dia = MyDialog(self.frame)
        #wx.CallLater(250, self.dia.EndModal, wx.ID_OK) # works!!
        #wx.CallLater(250, self.DoButtonEvt, self.dia.btn) # also works
        result = self.dia.ShowModal()
        return result
        
    def DoButtonEvt(self, btn):
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        btn.GetEventHandler().ProcessEvent(event)
        
        
class TestMyPanel(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.frame.Show()

    def tearDown(self):
        self.app.Destroy()

    def test_true(self):
        self.assertTrue(True)

    def test_fake(self):
        enabled = self.ShowPanel()
        self.assertTrue(enabled)

    def ShowPanel(self):
        self.pnl = MyPanel(self.frame)
        self.pnl.Show()
        enabled = self.pnl.IsEnabled()
        self.pnl.Destroy()
        return enabled

"""

if __name__ == '__main__':
    pass
    #unittest.main()

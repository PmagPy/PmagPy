"""
tests for make_magic
"""

import wx
import unittest
import os
#import ErMagicBuilder
import make_magic
import builder

WD = os.getcwd()

class TestMakeMagicMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = make_magic.MainFrame(WD, "zebra")
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
        self.assertEqual("main panel", str(self.pnl.GetName()))

    def test_specimen_button(self):
        window = self.does_top_window_exist(self.pnl, 'specimen_btn', 'specimen')
        self.assertTrue(window, 'er_specimens grid window was not created')
        self.assertIsInstance(window, make_magic.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_sample_button(self):
        window = self.does_top_window_exist(self.pnl, 'sample_btn', 'sample')
        self.assertTrue(window, 'er_samples grid window was not created')
        self.assertIsInstance(window, make_magic.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_site_button(self):
        window = self.does_top_window_exist(self.pnl, 'site_btn', 'site')
        self.assertTrue(window, 'er_sites grid window was not created')
        self.assertIsInstance(window, make_magic.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_location_button(self):
        window = self.does_top_window_exist(self.pnl, 'location_btn', 'location')
        self.assertTrue(window, 'er_locations grid window was not created')
        self.assertIsInstance(window, make_magic.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_ages_button(self):
        window = self.does_top_window_exist(self.pnl, 'age_btn', 'age')
        self.assertTrue(window, 'er_ages grid window was not created')
        self.assertIsInstance(window, make_magic.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def does_window_exist(self, parent, btn_name, window_name):
        """
        produces a click event on the button called btn_name,
        see if it produces the window called window_name
        """
        btn, window = None, None
        children = parent.GetChildren()
        for child in children:
            if child.GetName() == btn_name:
                btn = child
                break
        if not btn:
            return None
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        btn.GetEventHandler().ProcessEvent(event)
        for child in parent.GetChildren():
            if child.GetName() == window_name and not isinstance(child, wx.lib.buttons.GenButton):
                window = child
                break
        if not window:
            return None
        else:
            return window


    def does_top_window_exist(self, parent, btn_name, window_name):
        """
        produces a click event on the button called btn_name, 
        see if it produces a top-level window called window_name
        """
        btn = None
        children = parent.GetChildren()
        for child in children:
            if child.GetName() == btn_name:
                btn = child
                break
        if not btn:
            return None
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        btn.GetEventHandler().ProcessEvent(event)
        for wind in wx.GetTopLevelWindows():
            if wind.GetName() == window_name:
                return wind
        return None



class TestMakeMagicGridFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        #self.grid = GridFrame(self.ErMagic, self.WD, grid_type, grid_type, self.panel)
        ErMagic = builder.ErMagicBuilder(WD)
        ErMagic.init_default_headers()
        self.frame = make_magic.GridFrame(ErMagic, WD, "specimen", "specimen")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)


    def test_grid_is_created(self):
        """
        """
        self.assertTrue(self.frame.grid)


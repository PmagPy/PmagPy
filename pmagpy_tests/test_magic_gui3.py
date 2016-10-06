"""
tests for magic_gui
"""

import wx
import unittest
import os
import sys
import programs.magic_gui3 as magic_gui
import pmagpy.new_builder as nb
import dialogs.grid_frame3 as grid_frame
import dialogs.pmag_widgets as pmag_widgets

WD = os.path.join(sys.prefix, "pmagpy_data_files", "magic_gui", "3_0")



class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = magic_gui.MainFrame(WD, name="best frame ever")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        return

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertEqual("main panel", str(self.pnl.GetName()))
        self.assertEqual("best frame ever", str(self.frame.GetName()))
        self.assertEqual(magic_gui.MainFrame, type(self.frame))


    def test_data_object_is_created(self):
        self.assertEqual(nb.Contribution, type(self.frame.contribution))
        self.assertIn('measurements', self.frame.contribution.tables)
        self.assertIn('specimens', self.frame.contribution.tables)
        self.assertIn('samples', self.frame.contribution.tables)
        self.assertEqual('sr01g2', self.frame.contribution.tables['specimens'].df.index[1])


    def test_specimen_button(self):
        window = self.does_top_window_exist(self.pnl, 'specimens_btn', 'specimens')
        self.assertTrue(window, 'specimens grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_sample_button(self):
        window = self.does_top_window_exist(self.pnl, 'samples_btn', 'samples')
        self.assertTrue(window, 'samples grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_site_button(self):
        window = self.does_top_window_exist(self.pnl, 'sites_btn', 'sites')
        self.assertTrue(window, 'sites grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_location_button(self):
        window = self.does_top_window_exist(self.pnl, 'locations_btn', 'locations')
        self.assertTrue(window, 'locations grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_age_button(self):
        window = self.does_top_window_exist(self.pnl, 'ages_btn', 'ages')
        self.assertTrue(window, 'age grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())



    def does_top_window_exist(self, parent, btn_name, window_name):
        """
        produces a click event on the button called btn_name,
        see if it produces a top-level window called window_name
        """
        btn = None
        children = parent.GetChildren()
        print ", ".join([child.GetName() for child in children])
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


class TestMagICGUIMenu(unittest.TestCase):


    def setUp(self):
        self.app = wx.App()
        self.frame = magic_gui.MainFrame(WD, name="best frame ever")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        for wind in wx.GetTopLevelWindows():
            res = wind.Destroy()
        self.app.Destroy()
        os.chdir(WD)

    def test_that_all_menus_exist(self):
        """
        check that all expected menus were created
        and that each menu item is enabled
        """
        menu_names = ['File', 'Help ']
        menus = self.frame.MenuBar.Menus
        found_menus = []
        for menu, menu_name in menus:
            self.assertIsInstance(menu, wx.Menu)
            for item in menu.GetMenuItems():
                self.assertTrue(item.IsEnabled())
            self.assertIn(menu_name, menu_names)
            found_menus.append(menu_name)
        self.assertEqual(set(menu_names), set(found_menus))

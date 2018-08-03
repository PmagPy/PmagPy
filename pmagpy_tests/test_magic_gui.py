"""
tests for magic_gui
"""

import wx
import unittest
import os
from programs import magic_gui
from pmagpy import contribution_builder as cb
import dialogs
from dialogs import grid_frame3 as grid_frame
#import dialogs.pmag_widgets as pmag_widgets
from pmagpy import pmag
from pmagpy import data_model3 as data_model

# set constants
DMODEL = data_model.DataModel()
WD = pmag.get_test_WD()
PROJECT_WD = os.path.join(WD, "data_files", "magic_gui", "3_0")


class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = magic_gui.MainFrame(PROJECT_WD,
                                         name="best frame ever",
                                         dmodel=DMODEL)
        self.frame.get_wd_data()
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
#        wx.CallAfter(self.frame.Destroy)
#        wx.CallAfter(self.app.Destroy)
        for fname in ('locations.txt', 'sites.txt'):
            try:
                os.remove(os.path.join(PROJECT_WD, fname))
            except OSError:
                pass
        os.chdir(WD)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertEqual("main panel", str(self.pnl.GetName()))
        self.assertEqual("best frame ever", str(self.frame.GetName()))
        self.assertEqual(magic_gui.MainFrame, type(self.frame))


    def test_data_object_is_created(self):
        self.assertEqual(cb.Contribution, type(self.frame.contribution))
        self.assertIn('measurements', self.frame.contribution.tables)
        self.assertIn('specimens', self.frame.contribution.tables)
        self.assertIn('samples', self.frame.contribution.tables)
        self.assertEqual('sr01g2', self.frame.contribution.tables['specimens'].df.index[1])


    def test_specimen_button(self):
        window = self.does_top_window_exist(self.pnl, 'specimens_btn', 'specimens')
        self.assertTrue(window, 'specimens grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        wx.CallAfter(self.assertTrue,window.IsShown())

    def test_sample_button(self):
        window = self.does_top_window_exist(self.pnl, 'samples_btn', 'samples')
        self.assertTrue(window, 'samples grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        wx.CallAfter(self.assertTrue,window.IsShown())

    def test_site_button(self):
        window = self.does_top_window_exist(self.pnl, 'sites_btn', 'sites')
        self.assertTrue(window, 'sites grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        wx.CallAfter(self.assertTrue,window.IsShown())

    def test_location_button(self):
        window = self.does_top_window_exist(self.pnl, 'locations_btn', 'locations')
        self.assertTrue(window, 'locations grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        wx.CallAfter(self.assertTrue,window.IsShown())


    def test_age_button(self):
        window = self.does_top_window_exist(self.pnl, 'ages_btn', 'ages')
        self.assertTrue(window, 'age grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        wx.CallAfter(self.assertTrue,window.IsShown())


    def test_measurement_button(self):
        window = self.does_top_window_exist(self.pnl, 'measurements_btn', 'measurements')
        self.assertTrue(window, 'measurement grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertIsInstance(window.grid, dialogs.magic_grid3.HugeMagicGrid)
        wx.CallAfter(self.assertTrue,window.IsShown())



    def does_top_window_exist(self, parent, btn_name, window_name):
        """
        produces a click event on the button called btn_name,
        see if it produces a top-level window called window_name
        """
        btn = None
        children = parent.GetChildren()
        print(", ".join([child.GetName() for child in children]))
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
        self.frame = magic_gui.MainFrame(PROJECT_WD, name="best frame ever",
                                         dmodel=DMODEL)
        self.frame.get_wd_data()
        self.pnl = self.frame.GetChildren()[0]
        self.contribution = self.frame.contribution

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


    def test_show_mainframe(self):
        menus = self.frame.MenuBar.Menus
        fmenu, fmenu_name = menus[0]

        # once you have the correct menu
        show_id = fmenu.FindItem('Show main window')
        show_item = fmenu.FindItemById(show_id)

        self.frame.Hide()
        self.assertFalse(self.frame.IsShown())

        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], show_id)
        self.frame.GetEventHandler().ProcessEvent(event)
        self.assertTrue(self.frame.IsShown())

    def test_close_grid(self):
        self.frame.grid_frame = grid_frame.GridFrame(self.contribution, PROJECT_WD,
                                                     "specimens", "specimens")
        self.assertTrue(self.frame.grid_frame.IsShown())
        menus = self.frame.MenuBar.Menus
        fmenu, fmenu_name = menus[0]
        # once you have the correct menu
        close_id = fmenu.FindItem('Close current grid')
        close_item = fmenu.FindItemById(close_id)

        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], close_id)
        self.frame.GetEventHandler().ProcessEvent(event)

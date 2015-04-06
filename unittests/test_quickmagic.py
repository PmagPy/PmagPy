#!/usr/bin/env python

import unittest
import sys
import os
import wx
import wx.lib.inspection
import numpy as np
import ipmag
import QuickMagIC as qm

# get WD before all the QuickMagIC stuff starts to happen
WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')

class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = qm.MagMainFrame(WD)
        self.pnl = self.frame.GetChildren()[0]
        #wx.lib.inspection.InspectionTool().Show()

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled)
        self.assertEqual('quickmagic main panel', self.pnl.GetName())

    def test_click_button_one(self):
        """
        make sure import window is created when user clicks btn 1
        """
        window = self.does_window_exist('step 1', 'import_magnetometer_data')
        self.assertTrue(window)

    def test_click_button_two(self):
        """
        make sure orientation_magic window is created when user clicks btn 2
        """
        window = self.does_window_exist('step 2', 'calculate geographic directions')
        self.assertTrue(window)

    def test_click_button_three(self):
        """
        make sure ErMagicBuilder window is created when user clicks btn 3
        """
        window = self.does_window_exist('step 3', 'ErMagicBuilder')
        self.assertTrue(window)

    def test_click_demag_gui(self):
        """
        make sure demag_gui window is created when users clicks btn
        """
        window = self.does_window_exist('demag gui', 'demag gui')
        self.assertTrue(window)

    def test_click_thellier_gui(self):
        """
        make sure thellier_gui window is created when users clicks btn
        """

        window = self.does_window_exist('thellier gui', 'thellier gui')
        self.assertTrue(window)

    def test_click_download_magic(self):
        pass

    def test_click_upload_magic(self):
        pass

    def test_click_change_dir(self):
        """
        test that the change_directory button produces the expected results
        """
        def do_test():
            new_WD = self.frame.WD
            self.assertNotEqual(old_WD, new_WD)
            
        old_WD = self.frame.WD
        self.click_change_dir()
        wx.CallLater(2000, do_test)

    
    def click_change_dir(self):
        def cancel_dia():
            new_path = os.path.split(self.frame.WD)[0]
            self.frame.change_dir_dialog.SetPath(new_path)
            self.frame.on_finish_change_dir(self.frame.change_dir_dialog, False)
            #self.frame.change_dir_dialog.EndModal(wx.ID_CANCEL)
        btn = self.frame.change_dir_button
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())

        #btn.GetEventHandler().ProcessEvent(event)
        self.frame.on_change_dir_button(None, show=False)
        wx.CallLater(1, cancel_dia)
        # works if i just leave out this bloody line:
        # meaning, everything happens as in real operation, just without actually showing the modal dialog
        # hmph
        #self.frame.change_dir_dialog.ShowModal()
    
    def does_window_exist(self, btn_name, window_name):
        """
        produces a click event on the button called btn_name, see if it produces the window called window_name
        """
        btn, window = None, None
        pnl_children = self.pnl.GetChildren()
        for child in pnl_children:
            if child.GetName() == btn_name:
                btn = child
                break
        if not btn:
            return None
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        btn.GetEventHandler().ProcessEvent(event)
        frame_children = self.frame.GetChildren()
        for child in frame_children:
            if child.GetName() == window_name:
                window = child
                break
        if not window:
            return None
        else:
            return window



class TestMenus(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = qm.MagMainFrame(WD)
        self.pnl = self.frame.GetChildren()[0]
        #print dir(self.frame)
        print self.frame.MenuBar
        #print 'dir(self.frame.MenuBar)', dir(self.frame.MenuBar)
        print self.frame.MenuBar.Menus
        print 'self.frame.MenuBar.MenuCount', self.frame.MenuBar.MenuCount
        print self.frame.FindItemInMenuBar.__doc__

        

        
        #wx.lib.inspection.InspectionTool().Show()

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()

        
    def test_that_all_menus_exist(self):
        menu_names = ['File', 'Import', 'Analysis and Plots']
        menus = self.frame.MenuBar.Menus
        for menu, menu_name in menus:
            #print dir(menu)
            self.assertIsInstance(menu, wx.Menu)
            self.assertTrue(menu.IsEnabled)
            self.assertIn(menu_name, menu_names)


    def test_click_core_depthplot(self):
        def do_thing():
            print 'DO THING!!!!!!!!!'
            print '---'
            self.assertFalse(True)
        print 'doing click_core_depthplot'
        menus = self.frame.MenuBar.Menus
        for menu, menu_name in menus:
            print 'menu_name', menu_name
            #print dir(menu)
            print menu.MenuItems
            item_id = menu.FindItem("Remanence data vs. depth/height/age")
            print 'doc', menu.FindItem.__doc__
            item = menu.FindItemById(item_id)
            #print 'ITEM:', dir(item)
        print item.GetText()
        print item.Label
        #event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        print 'wx.EVT_MENU', wx.EVT_MENU
        print 'dir(wx.EVT_MENU)', dir(wx.EVT_MENU)
        print 'wx.EVT_MENU.evtType', wx.EVT_MENU.evtType
        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], item_id)
        print 'event!', event
        self.frame.GetEventHandler().ProcessEvent(event)
        # parent of Core_depthplot frame should be self.frame (I believe)
        core_window = None
        for window in self.frame.Children:
            if window.GetName() == 'core_depthplot':
                core_window = window
                break
        self.assertTrue(core_window.IsEnabled())
        print 'type(core_window)', type(core_window)
        print core_window.bSizer2 # choose_file
        print core_window.bSizer13  # radio_buttons (lab protocol)
        print core_window.bSizer14 # labeled_Text_field (step)
        
        call = wx.CallLater(1, do_thing)
        print do_thing
        wx.CallAfter(do_thing, 'arg')
        #do_thing()
        print 'call.HasRun()', call.HasRun()
        print 'after CallLater'






        

if __name__ == '__main__':
    unittest.main()
            

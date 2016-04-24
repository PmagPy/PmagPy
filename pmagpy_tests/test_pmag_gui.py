#!/usr/bin/env python

import unittest
import os
import sys
import wx
#import wx.lib.inspection
import programs.pmag_gui as pmag_gui
import dialogs.pmag_menu_dialogs as pmag_menu_dialogs

# get WD before all the Pmag GUI stuff starts to happen
WD = sys.prefix
project_WD = os.path.join(WD, 'pmagpy_data_files', 'testing', 'my_project')
core_depthplot_WD = os.path.join(WD, 'pmagpy_data_files',
                                 'testing', 'core_depthplot')


class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = pmag_gui.MagMainFrame(project_WD)
        self.pnl = self.frame.GetChildren()[0]
        #wx.lib.inspection.InspectionTool().Show()

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertTrue(self.pnl.IsShown())
        self.assertEqual('pmag_gui main panel', self.pnl.GetName())

    def test_click_button_one(self):
        """
        make sure import window is created when user clicks btn 1
        """
        print 'about to do test_click_button_one'
        window = self.does_window_exist('step 1', 'import_magnetometer_data')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_button_two(self):
        """
        make sure orientation_magic window is created when user clicks btn 2
        """
        window = self.does_window_exist('step 2', 'calculate geographic directions')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_click_button_three(self):
        """
        make sure ErMagicBuilder window is created when user clicks btn 3
        """
        window = self.does_window_exist('step 3', 'ErMagicBuilder')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_demag_gui(self):
        """
        make sure demag_gui window is created when users clicks btn
        """
        window = self.does_window_exist('demag gui', 'demag gui')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_thellier_gui(self):
        """
        make sure thellier_gui window is created when users clicks btn
        """

        window = self.does_window_exist('thellier gui', 'thellier gui')
        self.assertTrue(window)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


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
        print 'calling does_window_exist'
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
        self.app = wx.App()
        self.frame = pmag_gui.MagMainFrame(project_WD)
        self.pnl = self.frame.GetChildren()[0]

        #wx.lib.inspection.InspectionTool().Show()

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)


    def test_that_all_menus_exist(self):
        """
        check that all expected menus were created
        and that each menu item is enabled
        """
        menu_names = ['File', 'Help ', 'Import', 'Export', 'Analysis and Plots']
        menus = self.frame.MenuBar.Menus
        for menu, menu_name in menus:
            self.assertIsInstance(menu, wx.Menu)
            for item in menu.GetMenuItems():
                self.assertTrue(item.IsEnabled())
            self.assertIn(menu_name, menu_names)

    def test_click_any_file(self):
        window = self.does_window_exist('Import', "Import any file into your working directory", 'any file')
        self.assertTrue(window, 'Import any file window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_Azdip_format(self):
        window = self.does_window_exist('Import', 'AzDip format', 'azdip_window', submenu='orientation/location/stratigraphic files')
        self.assertTrue(window, 'Azdip import window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_IODP_sample_format(self):
        window = self.does_window_exist('Import', 'IODP Sample Summary csv file', 'IODP_samples', submenu='orientation/location/stratigraphic files')
        self.assertTrue(window, 'IODP samples import window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_Kly4s_format(self):
        window = self.does_window_exist('Import', 'kly4s format', 'kly4s', 'Anisotropy files')
        self.assertTrue(window, 'Kly4s import window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_SUFAR_asc_format(self):
        window = self.does_window_exist('Import', 'Sufar 4.0 ascii format', 'Sufar', 'Anisotropy files')
        self.assertTrue(window, 'SUFAR 4 ascii window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_agm_file_format(self):
        window = self.does_window_exist('Import', 'Import single agm file', 'agm_file', 'Hysteresis files')
        self.assertTrue(window, 'Import agm file window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_agm_folder_format(self):
        window = self.does_window_exist('Import', 'Import entire directory', 'agm_directory', 'Hysteresis files')
        self.assertTrue(window, 'Import agm folder window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_ani_depthplot(self):
        window = self.does_window_exist('Analysis and Plots', "Anisotropy data vs. depth/height/age", 'aniso_depthplot')
        self.assertTrue(window, 'Aniso_depthplot window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def test_click_core_depthplot(self):
        window = self.does_window_exist('Analysis and Plots', "Remanence data vs. depth/height/age", 'core_depthplot')
        self.assertTrue(window, 'Core_depthplot window was not created')
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())


    def does_window_exist(self, menu_name, menuitem_name, window_name, submenu=None):
        item = None
        menus = self.frame.MenuBar.Menus
        if submenu:
            for m, name in menus:
                if name == menu_name:
                    for m_item in m.MenuItems:
                        if m_item.Label == submenu:
                            menu = m_item.SubMenu
                            break
        else: # no submenu
            for m, name in menus:
                if name == menu_name:
                    menu = m
                    break
        # once you have the correct menu
        item_id = menu.FindItem(menuitem_name)
        item = menu.FindItemById(item_id)

        if not item:
            return None
        # generate command event with the relevant menuitem id
        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], item_id)
        self.frame.GetEventHandler().ProcessEvent(event)
        window = None
        # verify that the appropriate window was created
        for w in self.frame.Children:
            if w.GetName() == window_name:
                window = w
                break
        if not window:
            return None
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())
        return window
"""
@unittest.skip("just do it")
class TestCoreDepthplot(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = pmag_gui.MagMainFrame(core_depthplot_WD)
        self.pnl = self.frame.GetChildren()[0]
        self.core_window = pmag_menu_dialogs.core_depthplot(self.frame, self.frame.WD)


    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_core_depthplot_window_initializes(self):
        self.assertTrue(self.core_window.IsEnabled())
        self.assertTrue(self.core_window.IsShown())

    def test_run_core_depthplot_with_no_info(self):
        #print 'self.app', self.app
        def do_thing():
            pass
            #import sys
            #sys.exit() # the only thing that stops the modal
            #print 'in do_thing self.app:', self.app
            #print dir(dlg)
            #print 'dlg', dlg
            #print 'dlg.IsShown()', dlg.IsShown()
            #print 'dlg.IsModal()', dlg.IsModal()
            #dlg.Destroy()
            #print ')('
            #print 'doing thing'
            #print ')('
            #print 'self.app', self.app
            #self.app.Destroy()
            #print 'finished self.app.Destroy'
        btn = self.core_window.okButton
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, btn.GetId())
        #print event
        #wx.CallAfter(do_thing)
        #wx.CallLater(10000, do_thing)
        #btn.GetEventHandler().ProcessEvent(event)

        #text = "Something went wrong\nSee warnings in Terminal/Command Prompt and try again\nMake sure you have filled out all required fields"
        #dlg = wx.MessageDialog(None, message=text, caption="warning", style=wx.ICON_ERROR|wx.OK)
        #dlg.ShowModal()
        #print 'about to destroy!'
        #dlg.Destroy()

        #print self.core_window.bSizer2 # choose_file
        #print self.core_window.bSizer13  # radio_buttons (lab protocol)
        #print self.core_window.bSizer14 # labeled_Text_field (step)

    def test_run_core_depthplot_with_correct_info(self):
        "make sure a PlotFrame instance is created by running core_depthplot"
        radio_buttons = self.core_window.bSizer13.radio_buttons
        for rb in radio_buttons:
            if rb.Label == 'AF':
                rb.SetValue(True)
        self.core_window.bSizer14.text_field.SetValue('15')
        plot_frame = self.core_window.on_okButton(None)
        self.assertIsInstance(plot_frame, pmag_menu_dialogs.PlotFrame)
"""
#if __name__ == '__main__':
#    #unittest.main()
#    app = wx.App()
#    print 'app', app
#    app.frame = pmag_gui.MagMainFrame(project_WD)
#    print app.frame

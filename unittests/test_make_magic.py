"""
tests for make_magic
"""

import wx
import unittest
import os
#import ErMagicBuilder
import make_magic
import builder
import grid_frame
import pmag_widgets

WD = os.getcwd()

class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = make_magic.MainFrame(WD, "zebra")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        for wind in wx.GetTopLevelWindows():
            wind.Destroy()
            del wind
        self.app.Destroy()
        os.chdir(WD)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertEqual("main panel", str(self.pnl.GetName()))

    def test_data_object_is_created(self):
        self.assertTrue(self.frame.er_magic)

        self.assertFalse(self.frame.er_magic.specimens)
        self.assertFalse(self.frame.er_magic.samples)
        self.assertFalse(self.frame.er_magic.sites)
        self.assertFalse(self.frame.er_magic.locations)

        self.assertTrue(self.frame.er_magic.headers['specimen']['er'][0])
        self.assertTrue(self.frame.er_magic.headers['specimen']['er'][1])
        self.assertTrue(self.frame.er_magic.headers['specimen']['pmag'][0])
        self.assertTrue(self.frame.er_magic.headers['specimen']['pmag'][1])

    def test_pmag_results(self):
        self.assertTrue(self.frame.er_magic.headers['result']['pmag'][0])#pmag_results_header)
        self.assertTrue(self.frame.er_magic.headers['result']['pmag'][1])#pmag_results_reqd_header)

    def test_specimen_button(self):
        window = self.does_top_window_exist(self.pnl, 'specimen_btn', 'specimen')
        self.assertTrue(window, 'er_specimens grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_sample_button(self):
        window = self.does_top_window_exist(self.pnl, 'sample_btn', 'sample')
        self.assertTrue(window, 'er_samples grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_site_button(self):
        window = self.does_top_window_exist(self.pnl, 'site_btn', 'site')
        self.assertTrue(window, 'er_sites grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_location_button(self):
        window = self.does_top_window_exist(self.pnl, 'location_btn', 'location')
        self.assertTrue(window, 'er_locations grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_ages_button(self):
        window = self.does_top_window_exist(self.pnl, 'age_btn', 'age')
        self.assertTrue(window, 'er_ages grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
        self.assertTrue(window.IsEnabled())
        self.assertTrue(window.IsShown())

    def test_results_button(self):
        window = self.does_top_window_exist(self.pnl, 'result_btn', 'result')
        self.assertTrue(window, 'er_results grid window was not created')
        self.assertIsInstance(window, grid_frame.GridFrame)
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

class TestMainFrameWithData(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = make_magic.MainFrame(os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder'))
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

    def test_data_object_is_created(self):
        self.assertTrue(self.frame.er_magic)
        #self.assertTrue
        #self.assertTrue(self.frame.er_magic.specimens)
        

        self.assertTrue(self.frame.er_magic.specimens)
        self.assertTrue(self.frame.er_magic.samples)
        self.assertTrue(self.frame.er_magic.sites)
        self.assertTrue(self.frame.er_magic.locations)

        self.assertTrue(self.frame.er_magic.headers['specimen']['er'][0])#er_specimens_header)
        self.assertTrue(self.frame.er_magic.headers['specimen']['er'][1])#er_specimens_reqd_header)
        self.assertTrue(self.frame.er_magic.headers['specimen']['pmag'][0])#pmag_specimens_header)
        self.assertTrue(self.frame.er_magic.headers['specimen']['pmag'][1])#pmag_specimens_reqd_header)
        self.assertTrue(self.frame.er_magic.headers['sample']['pmag'][0])#pmag_samples_header)
        self.assertTrue(self.frame.er_magic.headers['sample']['er'][1])#er_samples_header)
        self.assertTrue(self.frame.er_magic.headers['site']['pmag'][0])#pmag_sites_header)#
        self.assertTrue(self.frame.er_magic.headers['site']['er'][0])#er_sites_header)

        specimen = self.frame.er_magic.specimens[0]
        sample = self.frame.er_magic.samples[0]
        site = self.frame.er_magic.sites[0]
        location = self.frame.er_magic.locations[0]
        self.assertFalse(specimen.results_data)
        self.assertTrue(specimen.er_data)
        self.assertTrue(specimen.pmag_data)
        self.assertTrue(sample.er_data)
        self.assertTrue(sample.pmag_data)
        self.assertTrue(site.er_data)
        self.assertTrue(site.pmag_data)
        self.assertTrue(location.er_data)
        self.assertFalse(location.pmag_data)

        #self.assertTrue(self.frame.er_magic.pmag_results_header)
        #self.assertTrue(self.frame.er_magic.pmag_results_reqd_header)

    def test_pmag_results(self):
        self.assertTrue(self.frame.er_magic.headers['result']['pmag'][0])#pmag_results_header)
        self.assertTrue(self.frame.er_magic.headers['result']['pmag'][1])#pmag_results_reqd_header)



class TestMakeMagicGridFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        #self.grid = GridFrame(self.ErMagic, self.WD, grid_type, grid_type, self.panel)
        ErMagic = builder.ErMagicBuilder(WD)
        ErMagic.init_default_headers()
        ErMagic.init_actual_headers()
        self.frame = grid_frame.GridFrame(ErMagic, WD, "specimen", "specimen")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_grid_is_created(self):
        """
        """
        self.assertTrue(self.frame.grid)

    @unittest.skip('This test calls ShowModal and stops everything')
    def test_add_cols(self):

        #event = wx.CommandEvent(wx.EVT_MENU.evtType[0], help_id)
        #self.frame.GetEventHandler().ProcessEvent(event)
        btn_id = self.frame.add_cols_button.Id
        
        event = wx.CommandEvent(wx.EVT_BUTTON.evtType[0], btn_id)
        self.frame.GetEventHandler().ProcessEvent(event)
        # oh, this sucks.  showmodal and all that


class TestMakeMagicMenu(unittest.TestCase):

    
    def setUp(self):
        self.app = wx.App()
        #self.grid = GridFrame(self.ErMagic, self.WD, grid_type, grid_type, self.panel)
        self.ErMagic = builder.ErMagicBuilder(WD)
        self.ErMagic.init_default_headers()
        self.ErMagic.init_actual_headers()
        self.frame = make_magic.MainFrame(WD)
        #self.frame = grid_frame.GridFrame(ErMagic, WD, "specimen", "specimen")
        #self.pnl = self.frame.GetChildren()[0]


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
        menu_names = ['File']
        menus = self.frame.MenuBar.Menus
        for menu, menu_name in menus:
            self.assertIsInstance(menu, wx.Menu)
            for item in menu.GetMenuItems():
                self.assertTrue(item.IsEnabled())
            self.assertIn(menu_name, menu_names)

    def test_click_help(self):
        """
        Test that help HtmlFrame is created
        """
        menus = self.frame.MenuBar.Menus
        fmenu, fmenu_name = menus[0]

        # once you have the correct menu
        help_id = fmenu.FindItem('Help')
        help_item = fmenu.FindItemById(help_id)

        top_windows = wx.GetTopLevelWindows()
        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], help_id)
        self.frame.GetEventHandler().ProcessEvent(event)
        top_windows = wx.GetTopLevelWindows()
        help_window = False
        for window in top_windows:
            if window.Label == 'Help Window':
                help_window = window
        self.assertTrue(help_window)
        self.assertTrue(help_window.IsEnabled())
        file_name = os.path.split(help_window.page)[1]
        self.assertEqual('make_magic.html', file_name)
        self.assertTrue(isinstance(help_window, pmag_widgets.HtmlFrame))

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
        self.frame.grid_frame = grid_frame.GridFrame(self.ErMagic, WD, "specimen", "specimen")
        self.assertTrue(self.frame.grid_frame.IsShown())
        menus = self.frame.MenuBar.Menus
        fmenu, fmenu_name = menus[0]
        # once you have the correct menu
        close_id = fmenu.FindItem('Close current grid')
        close_item = fmenu.FindItemById(close_id)

        event = wx.CommandEvent(wx.EVT_MENU.evtType[0], close_id)
        self.frame.GetEventHandler().ProcessEvent(event)



class TestMethodCodes(unittest.TestCase):

    
    def setUp(self):
        self.app = wx.App()
        #self.grid = GridFrame(self.ErMagic, self.WD, grid_type, grid_type, self.panel)
        self.method_WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'methods')
        self.ErMagic = builder.ErMagicBuilder(self.method_WD)
        self.ErMagic.get_all_magic_info()
        self.ErMagic.init_default_headers()
        self.ErMagic.init_actual_headers()
        self.frame = grid_frame.GridFrame(self.ErMagic, self.method_WD, "specimen", "specimen")

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        for wind in wx.GetTopLevelWindows():
            res = wind.Destroy()
        self.app.Destroy()
        os.chdir(WD)

    def test_write_codes_to_grid(self):
        spec = self.ErMagic.specimens[0]
        self.assertEqual('er_method_codes', spec.er_data['magic_method_codes'])
        self.assertEqual('pmag_method_codes', spec.pmag_data['magic_method_codes'])
        self.assertIn('magic_method_codes', self.frame.grid.col_labels)
        self.assertIn('magic_method_codes++', self.frame.grid.col_labels)

        col_ind = self.frame.grid.col_labels.index('magic_method_codes')
        cell_value = self.frame.grid.GetCellValue(0, col_ind)
        self.assertEqual(cell_value, 'er_method_codes')

        col_ind = self.frame.grid.col_labels.index('magic_method_codes++')
        cell_value = self.frame.grid.GetCellValue(0, col_ind)
        self.assertEqual(cell_value, 'pmag_method_codes')

    def test_something(self):
        other_WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.other_er_magic = builder.ErMagicBuilder(other_WD)
        self.other_er_magic.init_default_headers()
        self.other_er_magic.init_actual_headers()
        self.other_er_magic.get_all_magic_info()
        #self.frame = make_magic.MainFrame(self.method_WD)
        self.other_frame = grid_frame.GridFrame(self.other_er_magic, other_WD,
                                                "specimen", "specimen")
        spec = self.other_er_magic.specimens[0]

        #self.assertNotIn('magic_method_codes++', self.other_frame.grid.col_labels)



    def test_save_codes(self):
        spec = self.ErMagic.specimens[0]
        col_ind = self.frame.grid.col_labels.index('magic_method_codes')
        self.frame.grid.SetCellValue(0, col_ind, 'new_er_code')
        col_ind = self.frame.grid.col_labels.index('magic_method_codes++')
        self.frame.grid.SetCellValue(0, col_ind, 'new_pmag_code')
        self.assertEqual('er_method_codes', spec.er_data['magic_method_codes'])
        self.assertEqual('pmag_method_codes', spec.pmag_data['magic_method_codes'])
        self.frame.grid.changes = set([0])
        self.frame.onSave(None)
        self.assertEqual('new_er_code', spec.er_data['magic_method_codes'])
        self.assertEqual('new_pmag_code', spec.pmag_data['magic_method_codes'])


    def test_without_codes(self):
        other_WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.other_er_magic = builder.ErMagicBuilder(other_WD)
        self.other_er_magic.init_default_headers()
        self.other_er_magic.init_actual_headers()
        self.other_er_magic.get_all_magic_info()
        #self.frame = make_magic.MainFrame(self.method_WD)
        self.other_frame = grid_frame.GridFrame(self.other_er_magic, other_WD,
                                                "specimen", "specimen")
        spec = self.other_er_magic.specimens[0]
        self.assertNotIn('magic_method_codes', self.other_frame.grid.col_labels)
        self.assertNotIn('magic_method_codes++', self.other_frame.grid.col_labels)

    def test_codes_with_result_grid(self):
        # create empty result grid
        self.frame = grid_frame.GridFrame(self.ErMagic, self.method_WD, "result", "result")
        self.assertFalse(any(self.ErMagic.results))
        col_labels = [self.frame.grid.GetColLabelValue(col) for col in range(self.frame.grid.GetNumberCols())]
        method_col = col_labels.index('magic_method_codes')
        # fill in name and method codes for one result
        self.frame.grid.SetCellValue(0, 0, 'result1')
        self.frame.grid.SetCellValue(0, method_col, 'code1')
        self.frame.grid.changes = set([0])
        # save changes
        self.frame.onSave(None)
        # there should be a result in the data object, now, with a method code
        res = self.ErMagic.results[0]
        self.assertTrue(any(self.ErMagic.results))
        self.assertEqual('code1', res.pmag_data['magic_method_codes'])
        # make a result grid with that one result
        self.new_frame = grid_frame.GridFrame(self.ErMagic, self.method_WD, "result", "result")
        # test that the result (and method codes) are written to the new grid
        self.assertEqual('result1', self.new_frame.grid.GetCellValue(0, 0))
        self.assertEqual('code1', self.new_frame.grid.GetCellValue(0, method_col))




#!/usr/bin/env python

import unittest
import wx, os, shutil, sys
from numpy import array, isnan
from programs import thellier_gui
from pmagpy import pmag
import dialogs.thellier_interpreter as thellier_interpreter



@unittest.skipIf(any([arg for arg in sys.argv if 'discover' in arg]), 'seg fault when run with other tests')
class TestThellierGUI(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = thellier_gui.Arai_GUI(project_WD,test_mode=True,DM=2)
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        try: os.remove(os.path.join(project_WD, "rmag_anisotropy.txt"))
        except OSError: pass
        try: os.remove(os.path.join(project_WD, "rmag_anisotropy.log"))
        except OSError: pass
        try: os.remove(os.path.join(project_WD, "rmag_results.txt"))
        except OSError: pass
        os.chdir(WD)
        wx.CallAfter(self.app.Destroy)

    def test_spd(self):
        from SPD import spd
        print('spd', spd)

    def test_empty_dir(self):
        try:
            thellier_gui.Arai_GUI(empty_WD, DM=2)
        except SystemExit as ex:
            self.assertTrue(ex)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertTrue(self.pnl.IsShown())

    def test_auto_interpreter(self):
        self.run_ai_on_frame(self.frame)
        ai_menu = self.get_menu_from_frame(self.frame,'Auto Interpreter')
        ai_output_item_id = ai_menu.FindItem("&Open auto-interpreter output files")
        ai_output_event = wx.CommandEvent(wx.EVT_MENU.typeId, ai_output_item_id)
        ai_warn_item_id = ai_menu.FindItem("&Open auto-interpreter Warnings/Errors")
        ai_warn_event = wx.CommandEvent(wx.EVT_MENU.typeId, ai_warn_item_id)
        self.frame.ProcessEvent(ai_output_event)
        self.frame.ProcessEvent(ai_warn_event)

    def test_interpreter(self):
        THERMAL = True
        MICROWAVE = False
        interpreter = thellier_interpreter.thellier_auto_interpreter(self.frame.Data, self.frame.Data_hierarchy, self.frame.WD, self.frame.acceptance_criteria, self.frame.preferences, self.frame.GUI_log, THERMAL, MICROWAVE)
        program_ran, num_specs = interpreter.run_interpreter()
        self.assertTrue(program_ran)
        if self.frame.WD == os.path.join(WD, 'data_files', 'testing', 'my_project'):
            self.assertEqual(5, num_specs)

    def test_anisotropy_calc_and_warns(self):
        aniso_menu = self.get_menu_from_frame(self.frame,"Anisotropy")
        calc_aniso = wx.PyCommandEvent(wx.EVT_MENU.typeId, aniso_menu.FindItem("&Calculate anisotropy tensors"))
        warn_aniso = wx.PyCommandEvent(wx.EVT_MENU.typeId, aniso_menu.FindItem("&Show anisotropy calculation Warnings/Errors"))

        self.assertFalse(os.path.isfile(os.path.join(self.frame.WD, "rmag_anisotropy.txt")))
        self.assertFalse(os.path.isfile(os.path.join(self.frame.WD, "rmag_anisotropy.log")))
        self.assertFalse(os.path.isfile(os.path.join(self.frame.WD, "rmag_results.txt")))

        self.frame.ProcessEvent(calc_aniso)

        if self.frame.data_model!=3:
            self.assertTrue(os.path.isfile(os.path.join(self.frame.WD, "rmag_anisotropy.txt")))
            self.assertTrue(os.path.isfile(os.path.join(self.frame.WD, "rmag_anisotropy.log")))
            self.assertTrue(os.path.isfile(os.path.join(self.frame.WD, "rmag_results.txt")))

        self.frame.ProcessEvent(warn_aniso)

    def test_read_write_redo(self):
        analysis_menu = self.get_menu_from_frame(self.frame,"Analysis")
        write_redo_event = wx.PyCommandEvent(wx.EVT_MENU.typeId, analysis_menu.FindItem("&Save current interpretations to a 'redo' file"))
        read_redo_event = wx.PyCommandEvent(wx.EVT_MENU.typeId, analysis_menu.FindItem("&Import previous interpretation from a 'redo' file"))
        clear_interps_event = wx.PyCommandEvent(wx.EVT_MENU.typeId, analysis_menu.FindItem("&Clear all current interpretations"))

        self.run_ai_on_frame(self.frame)

        self.frame.ProcessEvent(write_redo_event)
        self.assertTrue(os.path.isfile(os.path.join(self.frame.WD, "thellier_GUI.redo")))

        old_interps = {sp : self.frame.Data[sp]['pars'] for sp in list(self.frame.Data.keys())}

        self.frame.ProcessEvent(clear_interps_event)
        cleared_vals = []
        [cleared_vals.extend(list(self.frame.Data[sp]['pars'].keys())) for sp in list(self.frame.Data.keys())]
        self.assertEqual(cleared_vals.count('lab_dc_field'), len(cleared_vals)/3)
        self.assertEqual(cleared_vals.count('er_specimen_name'), len(cleared_vals)/3)
        self.assertEqual(cleared_vals.count('er_sample_name'), len(cleared_vals)/3)

        self.frame.ProcessEvent(read_redo_event)
        new_interps = {sp : self.frame.Data[sp]['pars'] for sp in list(self.frame.Data.keys())}
        self.assertTrue(all([array(old_interps[k][k2]).all()==array(new_interps[k][k2]).all() if hasattr(old_interps[k][k2],'__iter__') else old_interps[k][k2]==new_interps[k][k2] for k in list(new_interps.keys()) for k2 in list(new_interps[k].keys()) if isinstance(old_interps[k][k2],float) and isinstance(new_interps[k][k2],float) and not isnan(old_interps[k][k2]) and not isnan(new_interps[k][k2])]))

        self.assertTrue(os.path.isfile(os.path.join(self.frame.WD, "thellier_GUI.redo")))
        try: os.remove(os.path.join(self.frame.WD, "thellier_GUI.redo"))
        except OSError: pass
        self.assertFalse(os.path.isfile(os.path.join(self.frame.WD, "thellier_GUI.redo")))

    def test_plot_paleoint_curve(self):
        plot_menu = self.get_menu_from_frame(self.frame,'Plot')
        plot_paleoint_event = wx.PyCommandEvent(wx.EVT_MENU.typeId, plot_menu.FindItem("&Plot paleointensity curve"))
        self.frame.ProcessEvent(plot_paleoint_event)
        self.run_ai_on_frame(self.frame)
        self.frame.ProcessEvent(plot_paleoint_event)

    def get_menu_from_frame(self,frame,menu_name):
        mb = frame.GetMenuBar()
        for m, n in mb.Menus:
            if n == menu_name or n == "&"+menu_name: return m

    def run_ai_on_frame(self,frame):
        ai_menu = self.get_menu_from_frame(frame,'Auto Interpreter')
        run_ai_item_id = ai_menu.FindItem('&Run Thellier auto interpreter')
        run_ai_event = wx.CommandEvent(wx.EVT_MENU.typeId, run_ai_item_id)
        frame.ProcessEvent(run_ai_event)

def backup(WD):
    print("backing up")
    #make backup directory
    backup_dir = os.path.join(WD,'.backup')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    #copy test files to backup
    src_files = os.listdir(WD)
    for file_name in src_files:
        full_file_name = os.path.join(WD, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, os.path.join(backup_dir,file_name))

def revert_from_backup(WD):
    print("reverting")
    backup_dir = os.path.join(WD,'.backup')
    #copy test files to backup
    src_files = os.listdir(backup_dir)
    for file_name in src_files:
        full_file_name = os.path.join(backup_dir, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, os.path.join(WD,file_name))
            os.remove(full_file_name)
    if os.path.exists(backup_dir):
        os.rmdir(backup_dir)

if __name__ == '__main__':
    # set constants
    WD = pmag.get_test_WD()
    project_WD = os.path.join(WD, 'data_files', 'testing', 'my_project')
    empty_WD = os.path.join(os.getcwd(), 'pmagpy_tests', 'examples', 'empty_dir')

    if '-d' in sys.argv:
        d_index = sys.argv.index('-d')
        project_WD = os.path.join(WD,sys.argv[d_index+1])
    elif '--dir' in sys.argv:
        d_index = sys.argv.index('--dir')
        project_WD = os.path.join(WD,sys.argv[d_index+1])

    backup(project_WD)
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestThellierGUI))
    revert_from_backup(project_WD)
else:
    WD = os.getcwd()
    project_WD = os.path.join(WD, 'data_files', 'testing', 'my_project')
    empty_WD = os.path.join(os.getcwd(), 'pmagpy_tests', 'examples', 'empty_dir')

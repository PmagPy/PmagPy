#!/usr/bin/env python

import unittest
import os
import wx
import sys
import wx.lib.inspection
import random as rn
from pmagpy.demag_gui_utilities import *
from programs import demag_gui

WD = sys.prefix
project_WD = os.path.join(os.getcwd(), 'pmagpy_tests', 'examples', 'demag_test_data')
#project_WD = os.path.join(os.getcwd(), 'tests', 'examples', 'my_project')
core_depthplot_WD = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
empty_WD = os.path.join(os.getcwd(), 'pmagpy_tests', 'examples', 'empty_dir')
allowable_float_error = 0.1

@unittest.skip("requires interaction")
class TestMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = demag_gui.Demag_GUI(project_WD)
        def clickOK():
            clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.frame.dlg.GetAffirmativeId())
            self.frame.dlg.ProcessEvent(clickEvent)
            if self.frame.dlg.IsModal:
                self.frame.dlg.EndModal(wx.ID_OK)
            self.frame.dlg.Close()
#        wx.CallAfter(clickOK)
        self.frame.clear_interpretations()

    def test_check_empty_dir(self):
        self.empty_frame = demag_gui.Demag_GUI(empty_WD)

    def test_to_str(self):
        str(self.frame)

    def test_add_delete_fit(self):
        add_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.add_fit_button.GetId())
        delete_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.delete_interpretation_button.GetId())

        menu_bar = self.frame.GetMenuBar()
        edit_menu = menu_bar.GetMenu(1)
        edit_menu_items = edit_menu.GetMenuItems()

        add_fit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu_items[0].GetId())
        delete_fit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu_items[1].GetId())

        #add fit with no bounds using menu
        self.frame.ProcessEvent(add_fit_menu_evt)
        self.assertEqual(len(self.frame.pmag_results_data['specimens'][self.frame.s]),1)
        #add fit with bounds using button
        tmin=self.frame.Data[self.frame.s]['zijdblock_steps'][0]
        tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-1]
        self.frame.tmin_box.SetValue(tmin)
        self.frame.tmax_box.SetValue(tmax)
        self.frame.ProcessEvent(add_fit_evt)
        self.assertEqual(len(self.frame.pmag_results_data['specimens'][self.frame.s]),2)
        self.assertEqual(self.frame.tmin_box.GetStringSelection(),tmin)
        self.assertEqual(self.frame.tmax_box.GetStringSelection(),tmax)
        self.assertEqual(self.frame.current_fit.tmin,tmin)
        self.assertEqual(self.frame.current_fit.tmax,tmax)

        self.frame.ProcessEvent(delete_fit_menu_evt)
        self.assertEqual(len(self.frame.pmag_results_data['specimens'][self.frame.s]),1)
        self.frame.ProcessEvent(delete_fit_evt)
        self.assertEqual(len(self.frame.pmag_results_data['specimens'][self.frame.s]),0)

    def test_next_prev_specimen(self):

        next_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.nextbutton.GetId())
        prev_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.prevbutton.GetId())

        #switch specimens using buttons
        s_old = self.frame.s
        self.frame.ProcessEvent(next_evt)
        self.assertNotEqual(self.frame.s,s_old)
        self.frame.ProcessEvent(prev_evt)
        self.assertEqual(self.frame.s,s_old)

        menu_bar = self.frame.GetMenuBar()
        edit_menu = menu_bar.GetMenu(1)
        edit_menu_items = edit_menu.GetMenuItems()

        next_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu_items[4].GetId())
        prev_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu_items[5].GetId())

        #switch specimens using menu option
        s_old = self.frame.s
        self.frame.ProcessEvent(next_menu_evt)
        self.assertNotEqual(self.frame.s,s_old)
        self.frame.ProcessEvent(prev_menu_evt)
        self.assertEqual(self.frame.s,s_old)

        #check edge case
        self.frame.ProcessEvent(prev_evt)
        self.assertEqual(self.frame.s,self.frame.specimens[-1])
        self.frame.ProcessEvent(next_evt)
        self.assertEqual(self.frame.s,self.frame.specimens[0])

    def test_fit_next_prev(self):
        menu_bar = self.frame.GetMenuBar()
        edit_menu = menu_bar.GetMenu(1)
        edit_menu_items = edit_menu.GetMenuItems()

        nextfit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu_items[2].GetId())
        prevfit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu_items[3].GetId())
        add_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.add_fit_button.GetId())

        self.frame.ProcessEvent(add_fit_evt)
        self.frame.ProcessEvent(add_fit_evt)
        self.frame.ProcessEvent(add_fit_evt)
        self.frame.ProcessEvent(add_fit_evt)
        fits = self.frame.pmag_results_data['specimens'][self.frame.s]
        ci = fits.index(self.frame.current_fit)

        for i in range(len(fits)+ci, ci, -1):
            self.assertEqual(fits[i%len(fits)], self.frame.current_fit)
            self.frame.ProcessEvent(nextfit_menu_evt)

        ci = fits.index(self.frame.current_fit)
        for i in range(ci, len(fits)+ci):
            self.assertEqual(fits[i%len(fits)], self.frame.current_fit)
            self.frame.ProcessEvent(prevfit_menu_evt)

    def test_mark_good_bad_meas(self):
        add_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.add_fit_button.GetId())
        delete_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.delete_interpretation_button.GetId())

        menu_bar = self.frame.GetMenuBar()
        edit_menu = menu_bar.GetMenu(1)
        edit_menu_items = edit_menu.GetMenuItems()
        mark_meas_data_menu = edit_menu_items[6].GetSubMenu()
        mark_meas_data_menu_items = mark_meas_data_menu.GetMenuItems()

        markgood_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,mark_meas_data_menu_items[0].GetId())
        markbad_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,mark_meas_data_menu_items[1].GetId())

        tmin_box_evt = wx.PyCommandEvent(wx.EVT_COMBOBOX.typeId,self.frame.tmin_box.GetId())
        tmax_box_evt = wx.PyCommandEvent(wx.EVT_COMBOBOX.typeId,self.frame.tmax_box.GetId())

        #add fit with bounds using button
        tmin=self.frame.Data[self.frame.s]['zijdblock_steps'][0]
        tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-1]
        self.frame.tmin_box.SetValue(tmin)
        self.frame.tmax_box.SetValue(tmax)
        self.frame.ProcessEvent(add_fit_evt)

        #check that the there is one fit and initialize basic variables for testing
        self.assertEqual(len(self.frame.pmag_results_data['specimens'][self.frame.s]),1)
        fit = self.frame.pmag_results_data['specimens'][self.frame.s][0]
        meas_data_before = self.frame.Data[self.frame.s]['measurement_flag']
        #mark first step good for the initial test
        self.frame.logger.Select(0)
        self.frame.ProcessEvent(markgood_menu_evt)
        total_num_of_good_meas_data =  len(filter(lambda x: x=='g', self.frame.Data[self.frame.s]['measurement_flag']))
        total_n = len(self.frame.Data[self.frame.s]['measurement_flag'])

        #insure that the fit spans all good meas data
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'],total_num_of_good_meas_data)
        #mark first step bad
        self.frame.logger.Select(0)
        self.frame.ProcessEvent(markbad_menu_evt)
        #check that first meas step is now bad
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'],total_num_of_good_meas_data-1)
        #mark first step good
        self.frame.logger.Select(0)
        self.frame.ProcessEvent(markgood_menu_evt)
        #reset value of fit used for interpretation
        self.frame.tmin_box.SetValue(tmin)
        self.frame.ProcessEvent(tmin_box_evt)
        #check that first step is good again
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'],total_num_of_good_meas_data)

        #mark a quarter of the meas data that is currently good bad to check iteration feature
        while self.frame.logger.GetSelectedItemCount() < int(total_num_of_good_meas_data/4):
            n = rn.randint(0,total_n-1)
            if not self.frame.logger.IsSelected(n) and \
               self.frame.Data[self.frame.s]['measurement_flag'][n] != 'b':
                self.frame.logger.Select(n)
        self.frame.ProcessEvent(markbad_menu_evt)
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'],total_num_of_good_meas_data-int(total_num_of_good_meas_data/4))

        #mark all meas data good to check good iteration filter and lack of change for good measurements already marked good
        for i in range(len(self.frame.Data[self.frame.s]['measurement_flag'])):
            self.frame.logger.Select(i)
        self.frame.ProcessEvent(markgood_menu_evt)
        #check all meas flags to insure all data is good
        for b in self.frame.Data[self.frame.s]['measurement_flag']:
            self.assertEqual(b, 'g')

        #reset bounds for fit
        self.frame.tmin_box.SetValue(tmin)
        self.frame.ProcessEvent(tmin_box_evt)
        self.frame.tmax_box.SetValue(tmax)
        self.frame.ProcessEvent(tmax_box_evt)

        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'], total_n)


        #check edge cases by marking first and last meas step bad
        self.frame.logger.Select(0)
        self.frame.logger.Select(self.frame.logger.GetItemCount()-1)
        self.frame.ProcessEvent(markbad_menu_evt)
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'], total_n-2)
        #mark them good again
        self.frame.logger.Select(0)
        self.frame.logger.Select(self.frame.logger.GetItemCount()-1)
        self.frame.ProcessEvent(markgood_menu_evt)
        #reset bounds for fit
        self.frame.tmin_box.SetValue(tmin)
        self.frame.ProcessEvent(tmin_box_evt)
        self.frame.tmax_box.SetValue(tmax)
        self.frame.ProcessEvent(tmax_box_evt)
        #check that all data is usable again
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'], total_n)

        #restore measurement data good/bad labels
        for i,b in enumerate(meas_data_before):
            if b == 'b': self.frame.logger.Select(i)
        self.frame.ProcessEvent(markbad_menu_evt)
        for i,b in enumerate(meas_data_before):
            if b == 'g': self.frame.logger.Select(i)
        self.frame.ProcessEvent(markgood_menu_evt)
        if self.frame.Data[self.frame.s]['measurement_flag'][0]=='b': total_num_of_good_meas_data+=1
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'],total_num_of_good_meas_data)

    def test_read_write_redo(self):
        self.frame.COORDINATE_SYSTEM = 'specimen'
        old_s = self.frame.s
        for specimen in self.frame.specimens:
            self.frame.s = specimen
            for i in range(len(self.frame.Data[specimen]['zijdblock'])):
                self.frame.mark_meas_good(i)
        self.frame.s = old_s
        self.frame.update_selection()

        self.assertFalse(self.frame.interpretation_editor_open)
        self.frame.on_menu_edit_interpretations(-1)
        self.assertTrue(self.frame.interpretation_editor_open)
        ie = self.frame.interpretation_editor

        addall_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.add_all_button.GetId())

        ie.ProcessEvent(addall_evt)
        ie.ProcessEvent(addall_evt)
        ie.ProcessEvent(addall_evt)

        menu_bar = self.frame.GetMenuBar()
        analysis_menu = menu_bar.GetMenu(2)
        analysis_menu_items = analysis_menu.GetMenuItems()

        importredo_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,analysis_menu_items[3].GetId())
        writeredo_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,analysis_menu_items[4].GetId())

        self.frame.ProcessEvent(writeredo_menu_evt)
        old_frame = str(self.frame)
        old_interpretations = []
        for speci in self.frame.pmag_results_data['specimens'].keys():
            old_interpretations += self.frame.pmag_results_data['specimens'][speci]

        self.frame.clear_interpretations()

        self.frame.ProcessEvent(importredo_menu_evt)
        imported_frame = str(self.frame)
        imported_interpretations = []
        for speci in self.frame.pmag_results_data['specimens'].keys():
            imported_interpretations += self.frame.pmag_results_data['specimens'][speci]

        for ofit,ifit in zip(old_interpretations,imported_interpretations):
            self.assertTrue(ofit.equal(ifit))

    def test_read_write_pmag_tables(self):
        old_s = self.frame.s
        for specimen in self.frame.specimens:
            self.frame.s = specimen
            for i in range(len(self.frame.Data[specimen]['zijdblock'])):
                self.frame.mark_meas_good(i)
        self.frame.s = old_s
        self.frame.update_selection()

        self.assertFalse(self.frame.interpretation_editor_open)
        self.frame.on_menu_edit_interpretations(-1)
        self.assertTrue(self.frame.interpretation_editor_open)
        ie = self.frame.interpretation_editor

        addall_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.add_all_button.GetId())

        ie.ProcessEvent(addall_evt)
        ie.ProcessEvent(addall_evt)
        ie.ProcessEvent(addall_evt)

        menu_bar = self.frame.GetMenuBar()
        file_menu = menu_bar.GetMenu(0)
        file_menu_items = file_menu.GetMenuItems()

        writepmag_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,file_menu_items[2].GetId())

        self.frame.ProcessEvent(writepmag_menu_evt)
        old_frame = str(self.frame)
        old_interpretations = []
        for speci in self.frame.pmag_results_data['specimens'].keys():
            old_interpretations += self.frame.pmag_results_data['specimens'][speci]

        frame2 = demag_gui.Demag_GUI(project_WD)

        old_s = frame2.s
        for specimen in frame2.specimens:
            frame2.s = specimen
            for i in range(len(frame2.Data[specimen]['zijdblock'])):
                frame2.mark_meas_good(i)
        frame2.s = old_s
        frame2.update_selection()

        imported_frame = str(frame2)
        imported_interpretations = []
        for speci in frame2.pmag_results_data['specimens'].keys():
            imported_interpretations += frame2.pmag_results_data['specimens'][speci]

        for ofit,ifit in zip(old_interpretations,imported_interpretations):
            self.assertTrue(ofit.equal(ifit))

    def test_ie_buttons(self):
        #test initialization of ie
        self.assertFalse(self.frame.interpretation_editor_open)
        self.frame.on_menu_edit_interpretations(-1)
        self.assertTrue(self.frame.interpretation_editor_open)
        ie = self.frame.interpretation_editor
        tmin=self.frame.Data[self.frame.s]['zijdblock_steps'][0]
        tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-1]
        tmin_index,tmax_index = self.frame.get_indices(None,tmin,tmax,self.frame.s)

        #set ie values for fit and create fits for all interpretations
        ie.tmin_box.SetValue(tmin)
        ie.tmax_box.SetValue(tmax)
        ie.name_box.WriteText("Test")
        if "goldenrod" in ie.color_dict.keys():
            ie.color_box.SetValue("goldenrod")
        self.assertEqual(ie.tmin_box.GetValue(),tmin)
        self.assertEqual(ie.tmax_box.GetValue(),tmax)
        self.assertEqual(ie.name_box.GetValue(),"Test")

        #create events to test ie
        addall_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.add_all_button.GetId())
        addhighlight_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.add_fit_button.GetId())
        delete_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.delete_fit_button.GetId())
        apply_change_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.apply_changes_button.GetId())

        #test add fit to all button
        ie.ProcessEvent(addall_evt)
        self.assertEqual(self.frame.current_fit,self.frame.pmag_results_data['specimens'][self.frame.s][0])

        #check fit parameters
        for speci in self.frame.specimens:
            fit = self.frame.pmag_results_data['specimens'][speci][0]
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")
        for fit,speci in ie.fit_list:
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")

        #test no highlighted items
        ie.ProcessEvent(addhighlight_evt)
        self.assertEqual(self.frame.total_num_of_interpertations(),len(self.frame.specimens))

        #alter parameters
        ie.name_box.SetValue("HighlightedTest")
        if "green" in ie.color_dict.keys():
            ie.color_box.SetValue("green")

        #highlight the first 2 specimens
        ie.logger.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.logger.SetItemState(1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.ProcessEvent(addhighlight_evt)

        #check the 2 fits that now should exist and check to make sure right number made
        self.assertEqual(self.frame.total_num_of_interpertations(),len(self.frame.specimens)+2)
        k0,k1 = self.frame.specimens[0],self.frame.specimens[1]
        new_fits = [[self.frame.pmag_results_data['specimens'][k0][1],k0]]
        new_fits.append([self.frame.pmag_results_data['specimens'][k1][1],k1])

        for fit,speci in new_fits:
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"HighlightedTest")

        #process delete event now that nothing is selected to ensure that nothing happens
        ie.ProcessEvent(delete_evt)

        #highlight and delete the 2 fits made during the highlight check
        ie.logger.SetItemState(1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.logger.SetItemState(3, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.ProcessEvent(delete_evt)
        self.assertEqual(self.frame.total_num_of_interpertations(),len(self.frame.specimens))

        #apply changes with nothing selected so nothing happens
        ie.ProcessEvent(apply_change_evt)

        #make sure all parameters are the same
        for speci in self.frame.specimens:
            fit = self.frame.pmag_results_data['specimens'][speci][0]
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")
        for fit,speci in ie.fit_list:
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")

        #revert so there is no difference between current fits and settings
        ie.tmin_box.SetValue(tmin)
        ie.tmax_box.SetValue(tmax)
        ie.name_box.SetValue("Test")
        if "goldenrod" in ie.color_dict.keys():
            ie.color_box.SetValue("goldenrod")
        self.assertEqual(ie.tmin_box.GetValue(),tmin)
        self.assertEqual(ie.tmax_box.GetValue(),tmax)
        self.assertEqual(ie.name_box.GetValue(),"Test")

        #highlight all of the listctrl
        for i in range(ie.logger.GetItemCount()):
            ie.logger.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.ProcessEvent(apply_change_evt)

        #make sure nothing changed
        for speci in self.frame.specimens:
            fit = self.frame.pmag_results_data['specimens'][speci][0]
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")
        for fit,speci in ie.fit_list:
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")

        #make changes to values so that interpretations are different
        tmin=self.frame.Data[self.frame.s]['zijdblock_steps'][1]
        tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-2]
        tmin_index,tmax_index = self.frame.get_indices(None,tmin,tmax,self.frame.s)

        ie.tmin_box.SetValue(tmin)
        ie.tmax_box.SetValue(tmax)
        ie.name_box.SetValue("OtherTest")
        if "pink" in ie.color_dict.keys():
            ie.color_box.SetValue("pink")
        self.assertEqual(ie.tmin_box.GetValue(),tmin)
        self.assertEqual(ie.tmax_box.GetValue(),tmax)
        self.assertEqual(ie.name_box.GetValue(),"OtherTest")

        #highlight all of the listctrl and apply changes
        for i in range(ie.logger.GetItemCount()):
            ie.logger.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.ProcessEvent(apply_change_evt)

        #make sure changes are right
        for fit,speci in ie.fit_list:
            tmin_index,tmax_index = self.frame.get_indices(fit,tmin,tmax,speci)
            gui_fit = self.frame.pmag_results_data['specimens'][speci][0]
            if tmin_index < 0:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
                self.assertEqual(gui_fit.tmin,self.frame.Data[speci]['zijdblock_steps'][0])
            elif tmin in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmin,tmin)
                self.assertEqual(gui_fit.tmin,tmin)
            else:
                self.assertEqual(fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
                self.assertEqual(gui_fit.tmin,self.frame.Data[speci]['zijdblock_steps'][tmin_index])
            if tmax_index > len(self.frame.Data[speci]['zijdblock_steps'])-1:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
                self.assertEqual(gui_fit.tmax,self.frame.Data[speci]['zijdblock_steps'][-1])
            elif tmax in self.frame.Data[speci]['zijdblock_steps']:
                self.assertEqual(fit.tmax,tmax)
                self.assertEqual(gui_fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
                self.assertEqual(gui_fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"OtherTest")

    def test_interpretation_accuracy(self):

        try:
            interps = read_LSQ(os.path.join(project_WD, 'SI4(80.2 to 100.7).LSQ'))
            self.frame.COORDINATE_SYSTEM = 'geographic'
            self.frame.read_from_LSQ(os.path.join(project_WD, 'SI4(80.2 to 100.7).LSQ'))
        except OSError: print("Could not read in LSQ file"); return
        except IOError: print("No LSQ file"); return

        for interp in interps:
            specimen = interp['er_specimen_name']
            gui_interps = self.frame.pmag_results_data['specimens'][specimen]
            similar_fit_present = True
            for gui_interp in gui_interps:
                pars = gui_interp.get('geographic')
                if int(pars['specimen_n']) != int(interp['specimen_n']): continue
                for value in ['specimen_dec','specimen_inc','specimen_mad','specimen_n']:
                    if round(float(pars[value]),1)-allowable_float_error > float(interp[value]) and float(interp[value]) > round(float(pars[value]),1)+allowable_float_error:
                        print(round(float(pars[value]),1),float(interp[value]))
                        similar_fit_present = False
            self.assertTrue(similar_fit_present)

    def tearDown(self):
        self.app.Destroy()
        try: os.remove(project_WD + "/demag_gui.redo")
        except OSError: pass
        try: os.remove(project_WD + "/pmag_specimens.txt")
        except OSError: pass
        try: os.remove(project_WD + "/pmag_sites.txt")
        except OSError: pass
        try: os.remove(project_WD + "/pmag_results.txt")
        except OSError: pass
        os.chdir(WD)

    def test_main_frame(self):
        self.assertTrue(self.frame)

if __name__ == '__main__':
    unittest.main()

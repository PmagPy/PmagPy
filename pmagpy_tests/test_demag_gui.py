#!/usr/bin/env python

import unittest
import os,wx,sys,shutil
import wx.lib.inspection
import random as rn
from pmagpy.demag_gui_utilities import *
import pmagpy.find_pmag_dir as find_pmag_dir
from programs import demag_gui


#@unittest.skipIf(sys.platform == 'darwin', 'these tests cause a seg fault on mac')
class TestDemagGUI(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = demag_gui.Demag_GUI(project_WD,write_to_log_file=False,test_mode_on=True)
        self.frame.clear_interpretations()

    def test_check_empty_dir(self):
        self.empty_frame = demag_gui.Demag_GUI(empty_WD,write_to_log_file=False,test_mode_on=True)

    def test_to_str(self):
        str(self.frame)

    def test_add_delete_fit(self):
        add_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.add_fit_button.GetId())
        delete_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.delete_fit_button.GetId())

        edit_menu = self.get_menu_from_frame(self.frame, "Edit")

        add_fit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu.FindItem("&New interpretation\tCtrl-N"))
        delete_fit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu.FindItem("&Delete interpretation\tCtrl-D"))

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
        self.assertEqual(self.frame.tmin_box.GetValue(),tmin)
        self.assertEqual(self.frame.tmax_box.GetValue(),tmax)
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

        edit_menu = self.get_menu_from_frame(self.frame, "Edit")

        next_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu.FindItem("&Next Specimen\tCtrl-Right"))
        prev_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu.FindItem("&Previous Specimen\tCtrl-Left"))

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
        edit_menu = self.get_menu_from_frame(self.frame, "Edit")

        nextfit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu.FindItem("&Next interpretation\tCtrl-Up"))
        prevfit_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,edit_menu.FindItem("&Previous interpretation\tCtrl-Down"))
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
        delete_fit_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,self.frame.delete_fit_button.GetId())

        edit_menu = self.get_menu_from_frame(self.frame, "Edit")
        mark_meas_data_menu = edit_menu.FindItemById(edit_menu.FindItem("&Flag Measurement Data")).GetSubMenu()

        markgood_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,mark_meas_data_menu.FindItem("&Good Measurement\tCtrl-Alt-G"))
        markbad_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,mark_meas_data_menu.FindItem("&Bad Measurement\tCtrl-Alt-B"))

        tmin_box_evt = wx.PyCommandEvent(wx.EVT_COMBOBOX.typeId,self.frame.tmin_box.GetId())
        tmax_box_evt = wx.PyCommandEvent(wx.EVT_COMBOBOX.typeId,self.frame.tmax_box.GetId())

        #add fit with bounds using button
        tmin=self.frame.Data[self.frame.s]['zijdblock_steps'][0]
        tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-1]
        for tmax_i in range(2,len(self.frame.Data[self.frame.s]['zijdblock_steps'])):
            if tmin!=tmax: tmax_i-=2; break
            else: tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-tmax_i]
        self.frame.ProcessEvent(add_fit_evt)
        self.frame.tmin_box.SetValue(tmin)
        self.frame.tmax_box.SetValue(tmax)
        self.frame.ProcessEvent(tmin_box_evt)

        #check that the there is one fit and initialize basic variables for testing
        self.assertEqual(len(self.frame.pmag_results_data['specimens'][self.frame.s]),1)
        fit = self.frame.pmag_results_data['specimens'][self.frame.s][0]
        meas_data_before = self.frame.Data[self.frame.s]['measurement_flag']
        #mark first step good for the initial test
        self.frame.logger.Select(0)
        self.frame.ProcessEvent(markgood_menu_evt)
        total_num_of_good_meas_data =  len([x for x in self.frame.Data[self.frame.s]['measurement_flag'] if x=='g'])
        total_num_of_good_meas_data-=tmax_i #account for the fact you might not be able to select all measurements if the last and first step are equal
        total_n = len(self.frame.Data[self.frame.s]['measurement_flag'])
        total_n-=tmax_i #this is the total n that can be selected between these bounds if you couldn't chose the top and bottom measurement you have to adjust

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
        self.frame.logger.Select(self.frame.logger.GetItemCount()-1-tmax_i)
        self.frame.ProcessEvent(markbad_menu_evt)
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'], total_n-2)
        #mark them good again
        self.frame.logger.Select(0)
        self.frame.logger.Select(self.frame.logger.GetItemCount()-1-tmax_i)
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
        if self.frame.Data[self.frame.s]['measurement_flag'][0]=='b': total_num_of_good_meas_data-=1
        elif self.frame.Data[self.frame.s]['measurement_flag'][-tmax_i]=='b': total_num_of_good_meas_data-=1
        self.assertEqual(fit.get(self.frame.COORDINATE_SYSTEM)['specimen_n'],total_num_of_good_meas_data)

    def test_read_write_redo(self):
        self.frame.COORDINATE_SYSTEM = 'specimen'
        self.mark_all_meas_good(self.frame)
        self.frame.update_selection()

        self.assertFalse(self.frame.ie_open)
        self.frame.on_menu_edit_interpretations(-1)
        self.assertTrue(self.frame.ie_open)
        ie = self.frame.ie

        addall_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.add_all_button.GetId())

        ie.ProcessEvent(addall_evt)
        ie.ProcessEvent(addall_evt)
        ie.ProcessEvent(addall_evt)

        file_menu = self.get_menu_from_frame(self.frame, "File")

        importredo_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,file_menu.FindItem("&Import interpretations from a redo file\tCtrl-R"))
        writeredo_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,file_menu.FindItem("&Save interpretations to a redo file\tCtrl-S"))

        self.frame.ProcessEvent(writeredo_menu_evt)
        old_frame = str(self.frame)
        old_interpretations = []
        for speci in list(self.frame.pmag_results_data['specimens'].keys()):
            old_interpretations += sorted(self.frame.pmag_results_data['specimens'][speci],key=fit_key)

        self.frame.clear_interpretations()

        self.frame.ProcessEvent(importredo_menu_evt)
        imported_frame = str(self.frame)
        imported_interpretations = []
        for speci in list(self.frame.pmag_results_data['specimens'].keys()):
            imported_interpretations += sorted(self.frame.pmag_results_data['specimens'][speci],key=fit_key)

        for ofit,ifit in zip(old_interpretations,imported_interpretations):
            self.assertTrue(ofit.equal(ifit))

    @unittest.skipIf(sys.platform == 'darwin', 'these tests cause a seg fault on mac')
    def test_read_write_pmag_tables(self):

        self.ie_add_n_fits_to_all(n_fits)

        file_menu = self.get_menu_from_frame(self.frame, "File")

        writepmag_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,file_menu.FindItem("&Save MagIC tables\tCtrl-Shift-S"))
        print("-------------------------------------------------------------")
        self.frame.ProcessEvent(writepmag_menu_evt)
        print("-------------------------------------------------------------")
        old_frame = str(self.frame)
        speci_with_fits = []
        old_interpretations = {}
        for speci in list(self.frame.pmag_results_data['specimens'].keys()):
            if self.frame.pmag_results_data['specimens'][speci] and \
               all([x.get('specimen') for x in self.frame.pmag_results_data['specimens'][speci]]):
                if speci not in speci_with_fits:
                    speci_with_fits.append(speci)
                old_interpretations[speci] = sorted(self.frame.pmag_results_data['specimens'][speci],key=fit_key)

        frame2 = demag_gui.Demag_GUI(project_WD,write_to_log_file=False,test_mode_on=True)

        frame2.update_selection()

        imported_frame = str(frame2)
        imported_interpretations = {}
        for speci in list(frame2.pmag_results_data['specimens'].keys()):
            if frame2.pmag_results_data['specimens'][speci] and \
               all([x.get('specimen') for x in frame2.pmag_results_data['specimens'][speci]]):
                if speci not in speci_with_fits:
                    speci_with_fits.append(speci)
                imported_interpretations[speci] = sorted(frame2.pmag_results_data['specimens'][speci],key=fit_key)

        for speci in speci_with_fits:
            if speci not in list(old_interpretations.keys()) or speci not in list(imported_interpretations.keys()): import pdb; pdb.set_trace()
            self.assertTrue(speci in list(old_interpretations.keys()))
            self.assertTrue(speci in list(imported_interpretations.keys()))
            for ofit,ifit in zip(old_interpretations[speci],imported_interpretations[speci]):
                self.assertTrue(ofit.equal(ifit))

    def test_ie_buttons(self):
        #mark all measurements good in RAM only so that there are no bad measurements causing endpoint changes (That's another test)
        self.mark_all_meas_good(self.frame)
        #test initialization of ie
        self.assertFalse(self.frame.ie_open)
        self.frame.on_menu_edit_interpretations(-1)
        self.assertTrue(self.frame.ie_open)
        ie = self.frame.ie
        tmin=self.frame.Data[self.frame.s]['zijdblock_steps'][0]
        tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-1]
        for i in range(2,len(self.frame.Data[self.frame.s]['zijdblock_steps'])):
            if tmin!=tmax: break
            else: tmax=self.frame.Data[self.frame.s]['zijdblock_steps'][-i]
        tmin_index,tmax_index = self.frame.get_indices(None,tmin,tmax,self.frame.s)

        #set ie values for fit and create fits for all interpretations
        ie.tmin_box.SetValue(tmin)
        ie.tmax_box.SetValue(tmax)
        ie.name_box.WriteText("Test")
        if "goldenrod" in list(ie.color_dict.keys()):
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
        valid_specs = 0
        for speci in self.frame.specimens:
            if tmin not in self.frame.Data[speci]['zijdblock_steps'] or \
               tmax not in self.frame.Data[speci]['zijdblock_steps'] or \
               speci not in self.frame.pmag_results_data['specimens'] or \
               len(self.frame.pmag_results_data['specimens'][speci])<1:
                continue
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
                if fit.tmax!=tmax: import pdb; pdb.set_trace()
                self.assertEqual(fit.tmax,tmax)
            else:
                self.assertEqual(fit.tmax,self.frame.Data[speci]['zijdblock_steps'][tmax_index])
            self.assertEqual(fit.name,"Test")
            valid_specs+=1
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
        self.assertEqual(self.frame.total_num_of_interpertations(),valid_specs)

        #alter parameters
        ie.name_box.SetValue("HighlightedTest")
        if "green" in list(ie.color_dict.keys()):
            ie.color_box.SetValue("green")

        #highlight the first 2 specimens
        ie.logger.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.logger.SetItemState(1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        ie.ProcessEvent(addhighlight_evt)

        #check the 2 fits that now should exist and check to make sure right number made
        self.assertEqual(self.frame.total_num_of_interpertations(),valid_specs+2)
        k0,k1 = ie.fit_list[0][1],ie.fit_list[1][1]
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
        wx.CallAfter(self.assertEqual,(self.frame.total_num_of_interpertations(),valid_specs))

        #apply changes with nothing selected so nothing happens
        ie.ProcessEvent(apply_change_evt)

        #make sure all parameters are the same
        for speci in self.frame.specimens:
            if len(self.frame.pmag_results_data['specimens'][speci])==0: continue
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
        if "goldenrod" in list(ie.color_dict.keys()):
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
            if tmin not in self.frame.Data[speci]['zijdblock_steps'] or \
               tmax not in self.frame.Data[speci]['zijdblock_steps'] or \
               speci not in self.frame.pmag_results_data['specimens'] or \
               len(self.frame.pmag_results_data['specimens'][speci])<1:
                continue
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
        if "pink" in list(ie.color_dict.keys()):
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

    def test_interpretation_accuracy_with_lsq(self):
        g = os.walk(project_WD)
        lsq_filenames = list([os.path.join(project_WD,x) for x in [x for x in next(g)[2] if x.lower().endswith('.lsq')]])
        for lsq_filename in lsq_filenames:
            try:
                interps = read_LSQ(lsq_filename)
                self.frame.COORDINATE_SYSTEM = 'geographic'
                self.frame.read_from_LSQ(lsq_filename)
            except OSError as e: print(("Could not read in LSQ file: %s"%lsq_filename)); raise e
            except IOError as e: print(("No LSQ file: %s"%lsq_filename)); raise e

            for interp in interps:
                specimen = interp['er_specimen_name']
                gui_interps = self.frame.pmag_results_data['specimens'][specimen]
                similar_fit_present = True
                for gui_interp in gui_interps:
                    pars = gui_interp.get('geographic')
                    if int(pars['specimen_n']) != int(interp['specimen_n']): continue
                    for value in ['specimen_dec','specimen_inc','specimen_mad','specimen_n']:
                        if round(float(pars[value]),1)-allowable_float_error > float(interp[value]) and float(interp[value]) > round(float(pars[value]),1)+allowable_float_error:
                            print((round(float(pars[value]),1),float(interp[value])))
                            similar_fit_present = False
                self.assertTrue(similar_fit_present)

    @unittest.skipIf(sys.platform == 'darwin', 'these tests cause a seg fault on mac')
    def test_VGP_viewer(self):
        tools_menu = self.get_menu_from_frame(self.frame, "Tools")

        viewVGPs_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, tools_menu.FindItem("&View VGPs\tCtrl-Shift-V"))
        self.frame.ProcessEvent(viewVGPs_menu_evt)

        self.ie_add_n_fits_to_all(n_fits)

        #test actual VGP calculation and display
        self.frame.ProcessEvent(viewVGPs_menu_evt)

    @unittest.skipIf(sys.platform == 'darwin', 'these tests cause a seg fault on mac')
    def test_check_sample_orientation_bad_good(self):
        analysis_menu = self.get_menu_from_frame(self.frame, "Analysis")
        check_sample_menu = analysis_menu.FindItemById(analysis_menu.FindItem("Sample Orientation")).GetSubMenu()

        check_orient_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, check_sample_menu.FindItem("&Check Sample Orientations\tCtrl-O"))
        mark_sample_bad_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, check_sample_menu.FindItem("&Mark Sample Bad\tCtrl-."))
        mark_sample_good_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, check_sample_menu.FindItem("&Mark Sample Good\tCtrl-,"))

        self.assertFalse(self.frame.check_orient_on)
        self.frame.ProcessEvent(check_orient_menu_evt)
        self.assertFalse(self.frame.check_orient_on)

        self.ie_add_n_fits_to_all(n_fits)

        self.assertFalse(self.frame.check_orient_on)
        self.frame.ProcessEvent(check_orient_menu_evt)
        wx.CallAfter(self.assertTrue,self.frame.check_orient_on)

        self.frame.ProcessEvent(mark_sample_bad_menu_evt)
        samp = self.frame.Data_hierarchy['sample_of_specimen'][self.frame.s]
        specs = self.frame.Data_hierarchy['samples'][samp]['specimens']
        for s in specs:
            for comp in self.frame.pmag_results_data['specimens'][s]:
                self.assertTrue(comp in self.frame.bad_fits)
                self.frame.mark_fit_good(comp,spec=s)
                self.assertTrue(comp in self.frame.bad_fits)

        self.frame.ProcessEvent(mark_sample_good_menu_evt)
        samp = self.frame.Data_hierarchy['sample_of_specimen'][self.frame.s]
        specs = self.frame.Data_hierarchy['samples'][samp]['specimens']
        for s in specs:
            for comp in self.frame.pmag_results_data['specimens'][s]:
                self.assertTrue(comp not in self.frame.bad_fits)

    def test_export_images(self):
        file_menu = self.get_menu_from_frame(self.frame, "File")
        export_images_menu = file_menu.FindItemById(file_menu.FindItem("&Save plot")).GetSubMenu()

        export_all_images_menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, export_images_menu.FindItem("&Save all plots"))

        self.frame.ProcessEvent(export_all_images_menu_evt)

    def ie_add_n_fits_to_all(self,n):
        #test initialization of ie
        tools_menu = self.get_menu_from_frame(self.frame, "Tools")
        open_ie_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, tools_menu.FindItem("&Interpretation editor\tCtrl-E"))
        self.frame.ProcessEvent(open_ie_evt)
        self.assertTrue(self.frame.ie_open)
        ie = self.frame.ie
        addall_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, ie.add_all_button.GetId())

        for i in range(n):
            steps = self.frame.Data[self.frame.s]['zijdblock_steps']
            tmin=steps[rn.randint(0,len(steps)-3)]
            tmax=steps[rn.randint(steps.index(tmin)+2,len(steps)-1)]
            ie.tmin_box.SetValue(tmin)
            ie.tmax_box.SetValue(tmax)
            ie.name_box.Clear()
            ie.name_box.WriteText("test%d"%i)
            self.assertEqual(ie.tmin_box.GetValue(),tmin)
            self.assertEqual(ie.tmax_box.GetValue(),tmax)
            self.assertEqual(ie.name_box.GetValue(),"test%d"%i)
            wx.CallAfter(ie.ProcessEvent, addall_evt)

    def get_menu_from_frame(self,frame,menu_name):
        mb = frame.GetMenuBar()
        for m, n in mb.Menus:
            if n == menu_name or n == "&"+menu_name: return m

    def mark_all_meas_good(self,frame):
        old_s = frame.s
        for specimen in frame.specimens:
            frame.s = specimen
            for i in range(len(frame.Data[specimen]['zijdblock'])):
                frame.mark_meas_good(i)
        frame.s = old_s

    def tearDown(self):
        wx.CallAfter(self.frame.Destroy)
        wx.CallAfter(self.app.Destroy)
        try: os.remove(os.path.join(project_WD, "demag_gui.redo"))
        except OSError: pass
        try: os.remove(os.path.join(project_WD, "pmag_specimens.txt"))
        except OSError: pass
        try: os.remove(os.path.join(project_WD, "pmag_sites.txt"))
        except OSError: pass
        try: os.remove(os.path.join(project_WD, "pmag_results.txt"))
        except OSError: pass
        os.chdir(WD)

    def test_main_frame(self):
        self.assertTrue(self.frame)

def fit_key(f1,f2=None):
    if f2==None: return 0
    for c1,c2 in zip(f1.name,f2.name):
        if ord(c1)==ord(c2): continue
        else: return ord(c1)-ord(c2)
    return 0

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

    WD = find_pmag_dir.get_pmag_dir()
    if '-d' in sys.argv:
        d_index = sys.argv.index('-d')
        project_WD = os.path.join(WD,sys.argv[d_index+1])
    elif '--dir' in sys.argv:
        d_index = sys.argv.index('--dir')
        project_WD = os.path.join(WD,sys.argv[d_index+1])
    else:
        project_WD = os.path.join(WD, 'pmagpy_tests', 'examples', 'demag_test_data')
    core_depthplot_WD = os.path.join(WD, 'data_files', 'core_depthplot')
    empty_WD = os.path.join(os.getcwd(), 'pmagpy_tests', 'examples', 'empty_dir')
    if '-e' in sys.argv:
        e_index = sys.argv.index('-e')
        allowable_float_error = float(sys.argv[e_index])
    elif '--error' in sys.argv:
        e_index = sys.argv.index('--error')
        allowable_float_error = float(sys.argv[e_index])
    else:
        allowable_float_error = 0.1
    n_fits = 3
    if '-n' in sys.argv:
        n_index = sys.argv.index('-n')
        n_fits = int(sys.argv[n_index+1])

    backup(project_WD)
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestDemagGUI))
    revert_from_backup(project_WD)
else:
    WD = find_pmag_dir.get_pmag_dir()
    project_WD = os.path.join(WD, 'pmagpy_tests', 'examples', 'demag_test_data')
    core_depthplot_WD = os.path.join(WD, 'data_files', 'core_depthplot')
    empty_WD = os.path.join(os.getcwd(), 'pmagpy_tests', 'examples', 'empty_dir')
    allowable_float_error = 0.1
    n_fits = 3

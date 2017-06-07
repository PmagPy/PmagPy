#!/usr/bin/env python
"""
assorted wxPython custom widgets
"""
# pylint: disable=W0612,C0111,C0103,C0301

import os
import wx
import wx.html
import webbrowser
# ******
from pmagpy.controlled_vocabularies3 import Vocabulary
#from pmagpy.controlled_vocabularies import vocab


# library for commonly used widgets.

class choose_file(wx.StaticBoxSizer):

    def __init__(self, parent, btn_text='add', method=None, remove_button=False):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(choose_file, self).__init__(box, orient=wx.VERTICAL)
        self.btn_text = btn_text
        self.method = method
        self.parent = parent
        self.file_path = wx.TextCtrl(self.parent, id=-1, size=(525, 25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(self.parent, id=-1, label=btn_text, name=btn_text)
        if method:
            self.parent.Bind(wx.EVT_BUTTON, method, self.add_file_button)
        text = "Choose file (no spaces are allowed in path):"
        self.Add(wx.StaticText(self.parent, label=text), flag=wx.ALIGN_LEFT)
        self.AddSpacer(4)
        if remove_button:
            if isinstance(remove_button, str):
                label = remove_button
            else:
                label = "remove file"
            rm_button = wx.Button(self.parent, id=-1, label=label, name="remove file")
            self.Add(rm_button, flag=wx.BOTTOM, border=4)
            self.parent.Bind(wx.EVT_BUTTON, self.on_remove_button, rm_button)
        bSizer0_1 = wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_file_button, wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(4)
        bSizer0_1.Add(self.file_path, wx.ALIGN_LEFT)
        self.Add(bSizer0_1, wx.ALIGN_LEFT)

    def on_remove_button(self, event):
        self.file_path.SetValue("")

    def return_value(self):
        return self.file_path.GetValue()

class NotEmptyValidator(wx.PyValidator):
    def __init__(self):
        print("initing validator")
        wx.PyValidator.__init__(self)

    def Clone(self):
        """
        Note that every validator must implement the Clone() method.
        """
        print("doing Clone")
        return NotEmptyValidator()

    def Validate(self, win):
        print("doing Validate")
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if len(text) == 0:
            print("textCtrl.Name:", textCtrl.Name)
            wx.MessageBox("{} must contain some text!".format(str(textCtrl.Name)), "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True

    def TransferToWindow(self):
        print("doing TransferToWindow")
        return True

    def TransferFromWindow(self):
        print("doing TransferFromWindow")
        return True


class choose_dir(wx.StaticBoxSizer):

    def __init__(self, parent, btn_text='add', method=None):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(choose_dir, self).__init__(box, orient=wx.VERTICAL)
        self.btn_text = btn_text
        self.parent = parent
        self.parent.dir_path = wx.TextCtrl(parent, id=-1, size=(400, 25), style=wx.TE_READONLY)
        self.add_dir_button = wx.Button(parent, id=-1, label=btn_text, name='add')
        if method:
            self.parent.Bind(wx.EVT_BUTTON, method, self.add_dir_button)
        text = "Choose folder (no spaces are allowed in path):"
        self.Add(wx.StaticText(self.parent, label=text), wx.ALIGN_LEFT)
        self.AddSpacer(4)
        bSizer0_1 = wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_dir_button, wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(4)
        bSizer0_1.Add(self.parent.dir_path, wx.ALIGN_LEFT)
        self.Add(bSizer0_1, wx.ALIGN_LEFT)

    def return_value(self):
        return self.parent.dir_path.GetValue()


class simple_text(wx.StaticBoxSizer):
    def __init__(self, parent, TEXT):
        self.parent = parent
        box = wx.StaticBox(self.parent, wx.ID_ANY, "")
        super(simple_text, self).__init__(box, orient=wx.HORIZONTAL)
        self.Add(wx.StaticText(self.parent, label=TEXT), wx.ALIGN_LEFT)


class labeled_text_field(wx.StaticBoxSizer):
    def __init__(self, parent, label="User name (optional)"):
        self.parent = parent
        box = wx.StaticBox(self.parent, wx.ID_ANY, "")
        super(labeled_text_field, self).__init__(box, orient=wx.HORIZONTAL)
        self.Add(wx.StaticText(self.parent, label=label), wx.ALIGN_LEFT)
        self.AddSpacer(4)
        self.text_field = wx.TextCtrl(self.parent, id=-1, size=(100, 25))
        self.Add(self.text_field, wx.ALIGN_LEFT)

    def return_value(self):
        return self.text_field.GetValue()


class labeled_spin_ctrl(wx.StaticBoxSizer):
    def __init__(self, parent, TEXT):
        self.parent = parent
        box = wx.StaticBox(self.parent, wx.ID_ANY, "")
        super(labeled_spin_ctrl, self).__init__(box, orient=wx.HORIZONTAL)
        text = wx.StaticText(self.parent, label=TEXT)
        self.spin_ctrl = wx.SpinCtrl(parent, value='5', initial=5)
        self.Add(text, flag=wx.RIGHT, border=5)
        self.Add(self.spin_ctrl)

    def return_value(self):
        return self.spin_ctrl.GetValue()


class labeled_yes_or_no(wx.StaticBoxSizer):
    def __init__(self, parent, TEXT, label1, label2):
        self.parent = parent
        box = wx.StaticBox(self.parent, wx.ID_ANY, "")
        super(labeled_yes_or_no, self).__init__(box, orient=wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.rb1 = wx.RadioButton(parent, label=label1, style=wx.RB_GROUP)
        self.rb1.SetValue(True)
        self.rb2 = wx.RadioButton(parent, label=label2)
        hbox.Add(self.rb1, wx.ALIGN_LEFT)
        hbox.AddSpacer(5)
        hbox.Add(self.rb2, wx.ALIGN_LEFT)
        text = wx.StaticText(self.parent, label=TEXT, style=wx.TE_CENTER)
        self.Add(text, wx.ALIGN_LEFT)
        self.Add(hbox)

    def return_value(self):
        if self.rb1.GetValue():
            return True
        return False


class specimen_n(wx.StaticBoxSizer):
    """-spc option (number of characters defining specimen from sample"""
    def __init__(self, parent, label="number of terminal characters that distinguish specimen from sample"):
        self.parent = parent
        box = wx.StaticBox(self.parent, wx.ID_ANY, "")
        super(specimen_n, self).__init__(box, orient=wx.HORIZONTAL)
        self.Add(wx.StaticText(self.parent, label=label), wx.ALIGN_LEFT)
        self.AddSpacer(4)
        self.spc = wx.SpinCtrl(self.parent, id=-1, size=(100, 25), min=0, max=9)
        self.spc.SetValue(0)
        self.Add(self.spc, wx.ALIGN_LEFT)

    def return_value(self):
        return self.spc.GetValue()


class select_ncn(wx.StaticBoxSizer):
    """provides box sizer with a drop down menu for the standard naming conventions"""
    ncn_keys = ('XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'names in orient.txt -- NOT CURRENTLY SUPPORTED', '[XXXX]YYY where XXXX is the site name, enter number of X')#, 'this is a synthetic and has no site name']
    def __init__(self, parent, ncn_keys=ncn_keys):
        self.parent = parent
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(select_ncn, self).__init__(box, orient=wx.VERTICAL)
        ncn_values = list(range(1, 8))
        self.sample_naming_conventions = dict(list(zip(ncn_keys, ncn_values)))
        self.select_naming_convention = wx.ComboBox(parent, -1, ncn_keys[0], size=(440, 25), choices=ncn_keys, style=wx.CB_READONLY)
        self.sample_naming_convention_char = wx.TextCtrl(parent, id=-1, size=(40, 25))
        label1 = wx.StaticText(parent, label="sample-site naming convention:", style=wx.TE_CENTER)
        label2 = wx.StaticText(parent, label="delimiter (if necessary):", style=wx.TE_CENTER)
        gridbSizer = wx.GridBagSizer(5, 10)
        gridbSizer.Add(label1, (0, 0))
        gridbSizer.Add(label2, (0, 1))
        gridbSizer.Add(self.select_naming_convention, (1, 0))
        gridbSizer.Add(self.sample_naming_convention_char, (1, 1))
        self.Add(gridbSizer, wx.ALIGN_LEFT)

    def return_value(self):
        selected_ncn = str(self.select_naming_convention.GetValue())
        ncn_number = self.sample_naming_conventions[selected_ncn]
        if ncn_number == 4 or ncn_number == 7: # these are the only two that require a delimiter
            char = self.sample_naming_convention_char.GetValue()
            if char:
                return str(ncn_number) + '-' + str(char)
            else:
                return str(ncn_number)
        else:
            return str(ncn_number)


class select_specimen_ocn(wx.StaticBoxSizer):
    def __init__(self, parent):
        self.parent = parent
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(select_specimen_ocn, self).__init__(box, orient=wx.VERTICAL)
        label = wx.StaticText(self.parent, label="Orientation:")
        ocn_keys = ["Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip i.e., field_dip is degrees from vertical down - the hade",
                    "Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip i.e., mag_azimuth is strike and field_dip is hade",
                    "Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip i.e.,  lab arrow same as field arrow, but field_dip was a hade.",
                    "lab azimuth and dip are same as mag_azimuth, field_dip",
                    "lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90",
                    "Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip"]
        ocn_values = list(range(1, 6))
        self.sample_orientation_conventions = dict(list(zip(ocn_keys, ocn_values)))
        self.select_orientation_convention = wx.ComboBox(parent, -1, ocn_keys[0], size=(705, 25), choices=ocn_keys, style=wx.CB_READONLY)
        self.Add(label, wx.ALIGN_LEFT)
        self.Add(self.select_orientation_convention, wx.ALIGN_LEFT)
        self.AddSpacer(8)

    def return_value(self):
        selected_ocn = str(self.select_orientation_convention.GetValue())
        return self.sample_orientation_conventions[selected_ocn]


class select_declination(wx.StaticBoxSizer):
    def __init__(self, parent):
        self.parent = parent
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(select_declination, self).__init__(box, orient=wx.VERTICAL)
        label1 = wx.StaticText(self.parent, label="Declination:")
        label2 = wx.StaticText(self.parent, label="if necessary")
        self.dec_box = wx.TextCtrl(self.parent, size=(40, 25))
        declination_keys = ["Use the IGRF DEC value at the lat/long and date supplied", "Use this DEC: ", "DEC=0, mag_az is already corrected in file", "Correct mag_az but not bedding_dip_dir"]
        declination_values = list(range(1, 4))
        self.dcn = dict(list(zip(declination_keys, declination_values)))
        self.select_dcn = wx.ComboBox(parent, -1, declination_keys[0], size=(405, 25), choices=declination_keys, style=wx.CB_READONLY)
        gridSizer = wx.GridSizer(2, 2, 5, 10)
        gridSizer.AddMany([label1, label2, self.select_dcn, self.dec_box])
        self.Add(gridSizer, wx.ALIGN_LEFT)
        self.AddSpacer(10)

    def return_value(self):
        selected_dcn = str(self.select_dcn.GetValue())
        dcn_number = self.dcn[selected_dcn]
        if dcn_number == 2:
            return str(dcn_number) + " " + self.dec_box.GetValue()
        else:
            return dcn_number


class replicate_measurements(wx.StaticBoxSizer):

    def __init__(self, parent):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(replicate_measurements, self).__init__(box, orient=wx.HORIZONTAL)
        text = "replicate measurements:"
        replicate_text = wx.StaticText(parent, label=text, style=wx.TE_CENTER)
        self.replicate_rb1 = wx.RadioButton(parent, -1, 'Average replicates', style=wx.RB_GROUP)
        self.replicate_rb1.SetValue(True)
        self.replicate_rb2 = wx.RadioButton(parent, -1, 'Import all replicates')
        self.Add(replicate_text, wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(self.replicate_rb1, wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(self.replicate_rb2, wx.ALIGN_LEFT)

    def return_value(self):
        """
        return boolean
        """
        if self.replicate_rb1.GetValue():
            return True
        else:
            return False


class mass_or_volume_buttons(wx.StaticBoxSizer):

    def __init__(self, parent):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(mass_or_volume_buttons, self).__init__(box, orient=wx.HORIZONTAL)
        text = "Is the final field mass or volume:"
        stat_text = wx.StaticText(parent, label=text, style=wx.TE_CENTER)
        self.rb1 = wx.RadioButton(parent, -1, 'Volume', style=wx.RB_GROUP)
        self.rb1.SetValue(True)
        self.rb2 = wx.RadioButton(parent, -1, 'Mass')
        self.Add(stat_text, wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(self.rb1, wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(self.rb2, wx.ALIGN_LEFT)

    def return_value(self):
        """
        return boolean
        """
        if self.rb1.GetValue():
            return 'v'
        else:
            return 'm'


class check_box(wx.StaticBoxSizer):

    def __init__(self, parent, text):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(check_box, self).__init__(box, orient=wx.VERTICAL)
        self.cb = wx.CheckBox(parent, -1, text)
        self.Add(self.cb, flag=wx.TOP|wx.BOTTOM, border=8)

    def return_value(self):
        return self.cb.GetValue()


class radio_buttons(wx.StaticBoxSizer):

    def __init__(self, parent, choices, label=None, orientation=wx.VERTICAL):
        box = wx.StaticBox(parent, -1, "")
        super(radio_buttons, self).__init__(box, orient=orientation)
        rb1 = wx.RadioButton(parent, label=choices[0], style=wx.RB_GROUP)
        rb1.SetValue(True)
        if label:
            self.Add(wx.StaticText(parent, label=label))
        self.Add(rb1)
        self.radio_buttons = [rb1]
        for choice in choices[1:]:
            rb = wx.RadioButton(parent, label=choice)
            self.Add(rb)
            self.radio_buttons.append(rb)

    def return_value(self):
        for rb in self.radio_buttons:
            val = rb.GetValue()
            if val:
                return rb.Label


class large_checkbox_window(wx.StaticBoxSizer):

    def __init__(self, parent, choices):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(large_checkbox_window, self).__init__(box, orient=wx.VERTICAL)

        self.gridSizer = wx.FlexGridSizer(23, 10, 9, 10)
        labels = [wx.StaticText(parent, label=choice) for choice in sorted(choices)]
        for label in labels:
            self.gridSizer.Add(label, flag=wx.ALIGN_RIGHT)
            text_control = wx.TextCtrl(parent)
            text_sizer = self.gridSizer.Add(text_control)
            if choices[label.Label]:
                text_control.SetValue(choices[label.Label])
        self.Add(self.gridSizer, wx.ALIGN_LEFT)

    def return_value(self):
        keys = []
        values = []
        for sizer in self.gridSizer.Children:
            if isinstance(sizer.GetWindow(), wx._controls.TextCtrl):
                values.append(str(sizer.GetWindow().GetValue()))
            else:
                keys.append(str(sizer.GetWindow().Label))
        data_dict = dict(list(zip(keys, values)))
        return [data_dict]


class check_boxes(wx.StaticBoxSizer):

    def __init__(self, parent, gridsize, choices, text):
        """
        __init__(self, parent, gridsize, choices, text)
        gridsize is a tuple in form of (rows, cols, vertical_gap, horizontal_gap)
        """
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(check_boxes, self).__init__(box, orient=wx.VERTICAL)

        gridSizer2 = wx.GridSizer(gridsize[0], gridsize[1], gridsize[2], gridsize[3])
        self.boxes = []
        for choice in choices:
            cb = wx.CheckBox(parent, -1, choice)
            self.boxes.append(cb)
            gridSizer2.Add(cb, wx.ALIGN_RIGHT)
        self.Add(wx.StaticText(parent, label=text), wx.ALIGN_LEFT)
        self.Add(gridSizer2, wx.ALIGN_RIGHT)
        self.AddSpacer(4)

    def return_value(self):
        checked = []
        for cb in self.boxes:
            if cb.GetValue():
                checked.append(str(cb.Label))
        return checked


class sampling_particulars(check_boxes):

    def __init__(self, parent):
        gridsize = (5, 2, 0, 0)
        text = "Sampling Particulars (select all that apply):"
        particulars = ["FS-FD: field sampling done with a drill", "FS-H: field sampling done with hand samples", "FS-LOC-GPS: field location done with GPS", "FS-LOC-MAP:  field location done with map", "SO-POM:  a Pomeroy orientation device was used", "SO-ASC:  an ASC orientation device was used", "SO-MAG: magnetic compass used for all orientations", "SO-SUN: sun compass used for all orientations", "SO-SM: either magnetic or sun used on all orientations", "SO-SIGHT: orientation from sighting"]
        super(sampling_particulars, self).__init__(parent, gridsize, particulars, text)

    def return_value(self):
        checked = super(sampling_particulars, self).return_value()
        particulars = [p.split(':')[0] for p in checked]
        particulars = ':'.join(particulars)
        return particulars


class lab_field(wx.StaticBoxSizer):

    def __init__(self, parent):
        box = wx.StaticBox(parent, wx.ID_ANY, "", size=(100, 100))
        super(lab_field, self).__init__(box, orient=wx.VERTICAL)
        text = "Lab field (leave blank if unnecessary). Example: 40 0 -90"
        self.file_info_text = wx.StaticText(parent, label=text, style=wx.TE_CENTER)
        self.file_info_Blab = wx.TextCtrl(parent, id=-1, size=(40, 25))
        self.file_info_Blab_dec = wx.TextCtrl(parent, id=-1, size=(40, 25))
        self.file_info_Blab_inc = wx.TextCtrl(parent, id=-1, size=(40, 25))
        gridbSizer3 = wx.GridSizer(2, 3, 0, 10)
        gridbSizer3.AddMany([(wx.StaticText(parent, label="B (uT)", style=wx.TE_CENTER), wx.ALIGN_LEFT),
                             (wx.StaticText(parent, label="dec", style=wx.TE_CENTER), wx.ALIGN_LEFT),
                             (wx.StaticText(parent, label="inc", style=wx.TE_CENTER), wx.ALIGN_LEFT),
                             (self.file_info_Blab, wx.ALIGN_LEFT),
                             (self.file_info_Blab_dec, wx.ALIGN_LEFT),
                             (self.file_info_Blab_inc, wx.ALIGN_LEFT)])
        self.Add(self.file_info_text, wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(gridbSizer3, wx.ALIGN_LEFT)

    def return_value(self):
        labfield = "{} {} {}".format(self.file_info_Blab.GetValue(), self.file_info_Blab_dec.GetValue(), self.file_info_Blab_inc.GetValue())
        if labfield.isspace():
            return ''
        return labfield

class site_lat_lon(wx.StaticBoxSizer):

    def __init__(self, parent):
        box = wx.StaticBox(parent, wx.ID_ANY, "", size=(100, 100))
        super(site_lat_lon, self).__init__(box, orient=wx.VERTICAL)
        text = "Lattitude and Longitude of Site"
        self.file_info_text = wx.StaticText(parent, label=text, style=wx.TE_CENTER)
        self.file_info_site_lat = wx.TextCtrl(parent, id=-1, size=(40, 25))
        self.file_info_site_lon = wx.TextCtrl(parent, id=-1, size=(40, 25))
        gridbSizer3 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer3.AddMany([(wx.StaticText(parent, label="Lattitude (degrees)", style=wx.TE_CENTER), wx.ALIGN_LEFT),
                             (wx.StaticText(parent, label="Longitude (degrees)", style=wx.TE_CENTER), wx.ALIGN_LEFT),
                             (self.file_info_site_lat, wx.ALIGN_LEFT),
                             (self.file_info_site_lon, wx.ALIGN_LEFT)])
        self.Add(self.file_info_text, wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(gridbSizer3, wx.ALIGN_LEFT)

    def return_value(self):
        latlon = "{} {}".format(self.file_info_site_lat.GetValue(), self.file_info_site_lon.GetValue())
        if latlon.isspace():
            return ''
        return latlon

class synthetic(wx.StaticBoxSizer):
    def __init__(self, parent):
        box = wx.StaticBox(parent, wx.ID_ANY, "if synthetic:")
        super(synthetic, self).__init__(box, orient=wx.VERTICAL)
        gridSizer = wx.GridSizer(2, 2, 3, 10)
        institution_text = wx.StaticText(parent, label="Institution (no spaces)", style=wx.TE_CENTER)
        self.institution_field = wx.TextCtrl(parent, id=-1, size=(200, 25))
        type_text = wx.StaticText(parent, label="Type (no spaces)", style=wx.TE_CENTER)
        self.type_field = wx.TextCtrl(parent, id=-1, size=(200, 25))
        gridSizer.AddMany([(institution_text, wx.ALIGN_LEFT),
                           (type_text, wx.ALIGN_LEFT),
                           (self.institution_field, wx.ALIGN_LEFT),
                           (self.type_field, wx.ALIGN_LEFT)])
        self.Add(gridSizer)

    def return_value(self):
        if self.institution_field.GetValue():
            return str(self.institution_field.GetValue()) + ' ' + str(self.type_field.GetValue())


class experiment_type(wx.StaticBoxSizer):
    exp_names = ('AF Demag', 'Thermal (includes thellier but not trm)', 'Shaw method', 'IRM (acquisition)', '3D IRM experiment', 'NRM only', 'TRM acquisition', 'double AF demag', 'triple AF demag (GRM protocol)', 'Cooling rate experiment', 'anisotropy experiment')

    def __init__(self, parent, experiment_names=exp_names):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(experiment_type, self).__init__(box, orient=wx.VERTICAL)
        num_rows = len(experiment_names) / 3
        if len(experiment_names) % 3 != 0:
            num_rows += 1
        gridSizer2 = wx.GridSizer(num_rows, 3, 0, 0)
        self.boxes = []

        text = "Experiment type (select all that apply):"
        for experiment in experiment_names:
            cb = wx.CheckBox(parent, -1, experiment)
            self.boxes.append(cb)
            gridSizer2.Add(cb, wx.ALIGN_RIGHT)
        self.Add(wx.StaticText(parent, label=text), wx.ALIGN_LEFT)
        self.Add(gridSizer2, wx.ALIGN_RIGHT)
        self.AddSpacer(4)

    def return_value(self):
        checked = []
        for cb in self.boxes:
            if cb.GetValue():
                checked.append(str(cb.Label))
        if not checked:
            return ''
        experiment_key = {'AF Demag': 'AF', 'Thermal (includes thellier but not trm)': 'T', 'Shaw method': 'S', 'IRM (acquisition)': 'I', '3D IRM experiment': 'I3d', 'NRM only': 'N', 'TRM acquisition': 'TRM', 'anisotropy experiment': 'ANI', 'double AF demag': 'D', 'triple AF demag (GRM protocol)': 'G', 'Cooling rate experiment': 'CR'}
        experiment_string = ''
        for ex in checked:
            experiment_string += experiment_key[ex] + ':'
        return experiment_string[:-1]


class hbox_grid(wx.BoxSizer):

    def __init__(self, parent, delete_row_method, data_type, grid):
        """
        Create horizontal box with grid manipulation buttons and bindings.
        """
        super(hbox_grid, self).__init__(wx.HORIZONTAL)
        self.deleteRowButton = wx.Button(parent, id=-1, label='Delete selected row(s)', name='delete_row_btn#')
        parent.Bind(wx.EVT_BUTTON, lambda event: delete_row_method(event, data_type), self.deleteRowButton)
        #parent.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, lambda event: select_row_method(event, self.deleteRo#wButton), grid)
        self.deleteRowButton.Disable()
        self.Add(self.deleteRowButton, flag=wx.ALIGN_LEFT)


class btn_panel(wx.BoxSizer):

    def __init__(self, SELF, panel):
        super(btn_panel, self).__init__(wx.HORIZONTAL)
        pnl = panel
        SELF.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        SELF.okButton.SetDefault()
        SELF.Bind(wx.EVT_BUTTON, SELF.on_okButton, SELF.okButton)

        SELF.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        SELF.Bind(wx.EVT_BUTTON, SELF.on_cancelButton, SELF.cancelButton)

        SELF.helpButton = wx.Button(pnl, wx.ID_ANY, '&Help')
        SELF.Bind(wx.EVT_BUTTON, SELF.on_helpButton, SELF.helpButton)

        self.Add(SELF.okButton, 0, wx.ALL, 5)
        self.Add(SELF.cancelButton, 0, wx.ALL, 5)
        self.Add(SELF.helpButton, 0, wx.ALL, 5)


class combine_files(wx.BoxSizer):

    def __init__(self, parent, text, DM=2):
        super(combine_files, self).__init__(wx.VERTICAL)
        self.parent = parent
        self.WD = self.parent.WD
        self.text = text
        self.DM = DM

        bSizer0a = wx.StaticBoxSizer(wx.StaticBox(self.parent.panel, wx.ID_ANY, ""), wx.HORIZONTAL)
        self.add_file_button = wx.Button(self.parent.panel, id=-1, label='add file', name='add')
        self.parent.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)
        self.add_all_files_button = wx.Button(self.parent.panel, id=-1, label="add all *" + text + " files", name='add_all')
        self.parent.Bind(wx.EVT_BUTTON, self.on_add_all_files_button, self.add_all_files_button)
        bSizer0a.AddSpacer(5)
        bSizer0a.Add(self.add_file_button, wx.ALIGN_LEFT)
        bSizer0a.AddSpacer(5)
        bSizer0a.Add(self.add_all_files_button, wx.ALIGN_LEFT)
        bSizer0a.AddSpacer(5)

        bSizer0b = wx.StaticBoxSizer(wx.StaticBox(self.parent.panel, wx.ID_ANY, ""), wx.VERTICAL)
        self.file_paths = wx.TextCtrl(self.parent.panel, id=-1, size=(400, 200), style=wx.TE_MULTILINE)
        bSizer0b.AddSpacer(5)
        bSizer0b.Add(wx.StaticText(self.parent.panel, label=text), wx.ALIGN_LEFT)
        bSizer0b.AddSpacer(5)
        bSizer0b.Add(self.file_paths, wx.ALIGN_LEFT)
        bSizer0b.AddSpacer(5)
        bSizer0b.Add(wx.StaticText(self.parent.panel, label="Will combine into one {} file".format(text)), wx.ALIGN_LEFT)

        self.Add(bSizer0a, wx.ALIGN_LEFT)
        self.Add(bSizer0b, wx.ALIGN_LEFT)
        self.on_add_all_files_button(None)

    def on_add_file_button(self, event):
        #make easier to read later but maintain path differences such that same named files in different directories are recognized
        dlg = wx.FileDialog(
            None, message="choose MagIC formatted measurement file",
            defaultDir=self.WD,
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            full_path = dlg.GetPath()
            if full_path not in [self.file_paths.GetLineText(line) for line in range(self.file_paths.GetNumberOfLines())]:
                self.file_paths.AppendText(full_path + "\n")

    def on_add_all_files_button(self, event):
        all_files = os.listdir(self.WD)
        files_already_listed = [str(self.file_paths.GetLineText(line)) for line in range(self.file_paths.GetNumberOfLines())]
        include_files = [f for f in files_already_listed if f]
        add_files = []
        for F in all_files:
            F = str(F)
            if len(F) > 6:
                if self.text in F:
                    # prevents adding binary files, as well as misc saved stuff
                    if "#" not in F and "~" not in F and not F.endswith('.pyc'):
                        # ignore er_* files and pmag_* files for DM 3
                        if (self.DM == 3):
                            if (F.startswith("er_")) or (F.startswith("pmag_")):
                                continue
                        # prevent adding files that are already listed
                        if str(F) not in include_files:
                            include_files.append(str(F))
                            add_files.append(str(F))
        for f in add_files:
            self.file_paths.AppendText(f+"\n")


class LinkEnabledHtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())

class HtmlFrame(wx.Frame):
    """ This window displays a HtmlWindow """
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, None, wx.ID_ANY, title="Help Window", size=(600, 400))
        self.page = kwargs.get('page', 'http://earthref.org/MagIC/shortlists/')
        htmlwin = LinkEnabledHtmlWindow(self)
        htmlwin.LoadPage(self.page)
        htmlwin.Fit()

class YesNoCancelDialog(wx.Dialog):
    def __init__(self, parent, msg, title):
        super(YesNoCancelDialog, self).__init__(parent, wx.ID_ANY, title)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        text_box = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY), wx.VERTICAL)
        text = wx.StaticText(self, label=msg)
        text_box.Add(text)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_yes = wx.Button(self, wx.ID_ANY, label="Write and exit grid")
        btn_no = wx.Button(self, wx.ID_ANY, label="Exit grid")
        self.Bind(wx.EVT_BUTTON, self.on_btn_no, btn_no)
        self.Bind(wx.EVT_BUTTON, self.on_btn_yes, btn_yes)
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Continue editing")
        hbox.Add(btn_yes, flag=wx.ALIGN_CENTRE|wx.ALL, border=5)
        hbox.Add(btn_no, flag=wx.ALIGN_CENTRE|wx.ALL, border=5)
        hbox.Add(btn_cancel, flag=wx.ALIGN_CENTRE|wx.ALL, border=5)
        btn_yes.SetDefault()

        main_sizer.Add(text_box, flag=wx.ALIGN_CENTRE|wx.ALL, border=5)
        main_sizer.Add(hbox, flag=wx.ALIGN_CENTRE|wx.ALL, border=5)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre()

    def on_btn_no(self, event):
        self.Destroy()
        self.EndModal(wx.ID_NO)
        #return wx.ID_NO

    def on_btn_yes(self, event):
        self.Destroy()
        self.EndModal(wx.ID_YES)


class TextDialog(wx.Dialog):
    """
    Dialog window that returns a text string provided by user on ok button
    """
    def __init__(self, parent, label):
        super(TextDialog, self).__init__(parent, title='Provide text')
        self.text_ctrl = labeled_text_field(self, label)
        bsizer = wx.BoxSizer(wx.VERTICAL)

        btn_ok = wx.Button(self, wx.ID_OK, label="OK")
        btn_ok.SetDefault()
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Cancel")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(btn_ok, flag=wx.ALIGN_CENTER|wx.ALL, border=10)
        hbox.Add(btn_cancel, flag=wx.ALIGN_CENTER|wx.ALL, border=10)

        bsizer.Add(self.text_ctrl, flag=wx.ALIGN_CENTER|wx.ALL, border=10)
        bsizer.Add(hbox, flag=wx.ALIGN_CENTER)

        self.SetSizer(bsizer)
        bsizer.Fit(self)
        self.Centre()

class HeaderDialog(wx.Dialog):
    """
    Dialog window with one or two listboxes with items.
    As user clicks or double clicks, items are added to or removed from the selection,
    which is displayed in a text control.
    """
    def __init__(self, parent, label, items1=None, groups=False, items2=None):
        super(HeaderDialog, self).__init__(parent, title='Choose headers', size=(500, 500))
        if groups:
            word = 'Groups'
        else:
            word = 'Headers'
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        listbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if items1:
            box1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, word, name='box1'), wx.HORIZONTAL)
            listbox1 = wx.ListBox(self, wx.ID_ANY, choices=items1, style=wx.LB_MULTIPLE, size=(200, 350))
            box1.Add(listbox1)
            listbox_sizer.Add(box1, flag=wx.ALL, border=5)
            self.Bind(wx.EVT_LISTBOX, self.on_click, listbox1)
            self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_click, listbox1)
        if items2:
            box2 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Headers for interpretation data", name='box2'), wx.HORIZONTAL)
            listbox2 = wx.ListBox(self, wx.ID_ANY, choices=items2, style=wx.LB_MULTIPLE, size=(200, 350))
            box2.Add(listbox2)
            listbox_sizer.Add(box2, flag=wx.ALL, border=5)
            self.Bind(wx.EVT_LISTBOX, self.on_click, listbox2)
            self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_click, listbox2)


        text_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, 'Adding {}:'.format(word.lower()), name='text_box'),
                                     wx.HORIZONTAL)
        self.text_ctrl = wx.TextCtrl(self, id=-1, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(420, 100))
        text_sizer.Add(self.text_ctrl)

        btn_ok = wx.Button(self, wx.ID_OK, label="OK")
        btn_ok.SetDefault()
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Cancel")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(btn_ok, flag=wx.ALIGN_CENTER|wx.ALL, border=10)
        hbox.Add(btn_cancel, flag=wx.ALIGN_CENTER|wx.ALL, border=10)

        main_sizer.Add(listbox_sizer, flag=wx.ALIGN_CENTER)
        main_sizer.Add(text_sizer, flag=wx.ALIGN_CENTER)
        main_sizer.Add(hbox, flag=wx.ALIGN_CENTER)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        self.text_list = []

    def on_click(self, event):
        new_string = event.GetString()
        if new_string in self.text_list:
            self.text_list.remove(new_string)
        else:
            self.text_list.append(new_string)
        display_string = ', '.join(self.text_list)
        self.text_ctrl.SetValue(display_string)


class ComboboxDialog(wx.Dialog):
    """
    Dialog window that returns a text string provided by selection from combobox
    """
    def __init__(self, parent, label, items):
        super(ComboboxDialog, self).__init__(parent, title='Provide text')
        text_box = wx.StaticText(self, label=label)
        self.combobox = wx.ComboBox(self, wx.ID_ANY, items[0], choices=items, style=wx.CB_READONLY)
        bsizer = wx.BoxSizer(wx.VERTICAL)

        btn_ok = wx.Button(self, wx.ID_OK, label="OK")
        btn_ok.SetDefault()
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Cancel")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(btn_ok, flag=wx.ALIGN_CENTER|wx.ALL, border=10)
        hbox.Add(btn_cancel, flag=wx.ALIGN_CENTER|wx.ALL, border=10)

        bsizer.Add(text_box, flag=wx.TOP|wx.LEFT, border=10)
        bsizer.Add(self.combobox, flag=wx.ALIGN_CENTER|wx.ALL, border=10)
        bsizer.Add(hbox, flag=wx.ALIGN_CENTER)

        self.SetSizer(bsizer)
        bsizer.Fit(self)
        self.Centre()



class AddItem(wx.Frame):
    """This window allows user to add a new item (sample, site, or location)"""

    def __init__(self, parent, title, data_method, owner_items=None, belongs_to=None):
        self.title = title
        self.owner_items = owner_items
        self.belongs_to = belongs_to
        self.onAdd = data_method # data parsing method passed in by pmag_basic_dialogs
        wx.Frame.__init__(self, parent, wx.ID_ANY, title=self.title)
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.item_name = labeled_text_field(panel, label="{} Name: ".format(self.title))
        vbox.Add(self.item_name)
        if self.owner_items:
            owner_box = wx.StaticBox(panel, wx.ID_ANY, "")
            owner_boxSizer = wx.StaticBoxSizer(owner_box)
            items = self.owner_items
            owner_label = wx.StaticText(panel, label="Belongs to {}: ".format(self.belongs_to), style=wx.TE_CENTER)
            self.owner_name = wx.ComboBox(panel, -1, items[0], choices=items, style=wx.CB_READONLY)
            owner_boxSizer.Add(owner_label, flag=wx.RIGHT, border=5)
            owner_boxSizer.Add(self.owner_name)
            vbox.Add(owner_boxSizer)
        button_panel = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(panel, wx.ID_ANY, '&Add {}'.format(self.title))
        cancelButton = wx.Button(panel, wx.ID_ANY, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_okButton, okButton)
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, cancelButton)
        button_panel.AddMany([okButton, cancelButton])
        vbox.Add(button_panel)
        vbox.AddSpacer(10)

        panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Centre()
        self.Show()

    def on_cancelButton(self, event):
        self.Destroy()

    def on_okButton(self, event):
        item = str(self.item_name.return_value())
        if self.owner_items:
            owner = str(self.owner_name.GetValue())
            self.onAdd(item, owner)
        else:
            self.onAdd(item, None)
        self.Destroy()


class MethodCodeDemystifier(wx.StaticBoxSizer):

    def __init__(self, parent, vocabulary=None):
        """
        Takes a wx Parent window, and optionally a Vocabulary object
        """
        self.box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(MethodCodeDemystifier, self).__init__(self.box, orient=wx.VERTICAL)
        grid_sizer = wx.GridSizer(0, 5, 3, 3)
        if vocabulary:
            vc = vocabulary
        else:
            vc = Vocabulary()
        self.vc = vc
        types = vc.code_types.index
        types = vc.code_types['label']
        type_ind = vc.code_types.index

        for method_type in types:
            name = str(vc.code_types[vc.code_types.label == method_type].index[0])
            # make button & add to sizer
            btn = wx.Button(parent, label=method_type, name=name)
            grid_sizer.Add(btn, 0, wx.EXPAND)
            parent.Bind(wx.EVT_BUTTON, self.on_code_button, btn)

        self.Add(grid_sizer)
        width, height = grid_sizer.Size
        self.descriptions = wx.TextCtrl(parent, size=(800, 140), style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)#, value=init_text)
        self.Add(self.descriptions, flag=wx.ALIGN_CENTRE|wx.ALL, border=10)
        self.on_code_button(None, 'anisotropy_estimation')

    def on_code_button(self, event=None, meth_type=None):
        if not event and not meth_type:
            return
        if not event:
            code_name = meth_type
        else:
            btn = event.EventObject
            code_name = btn.Name
        meth_type = self.vc.get_one_meth_type(code_name, self.vc.all_codes)['definition']
        str_meths = [ind + " :  " + (meth_type[ind] or 'No description available') for ind in meth_type.index]
        res = '\n'.join(str_meths)
        self.descriptions.SetValue(res)



class ChooseOne(wx.Dialog):

    def __init__(self, parent, yes, no, text=""):
        super(ChooseOne, self).__init__(parent)
        self.yes = yes
        self.no = no
        self.text = text
        self.InitUI()
        self.SetTitle("Choose one")


    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        btn_yes = wx.Button(self, label=self.yes)
        btn_no = wx.Button(self, label=self.no)
        btn_yes.SetDefault()

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        if self.text:
            textBox = wx.StaticText(self, wx.ID_ANY, label=self.text)
            hbox1.Add(textBox, flag=wx.ALL, border=5)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(btn_yes)
        hbox2.Add(btn_no, flag=wx.LEFT, border=20)

        self.Bind(wx.EVT_BUTTON, self.on_yes, btn_yes)
        self.Bind(wx.EVT_BUTTON, self.on_no, btn_no)
        vbox.Add(hbox1,
                 flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)


        vbox.Add(hbox2,
                 flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)
        vbox.Fit(self)

    def on_yes(self, event):
        self.Destroy()
        self.EndModal(wx.ID_YES)

    def on_no(self, event):
        self.Destroy()
        self.EndModal(wx.ID_NO)


# assorted useful methods!

def on_add_dir_button(SELF, text):
    dlg = wx.DirDialog(
        None, message=text,
        defaultPath=os.getcwd(),
        style=wx.FD_OPEN | wx.DD_DEFAULT_STYLE
    )
    if dlg.ShowModal() == wx.ID_OK:
        SELF.parent.dir_path.SetValue(str(dlg.GetPath()))
    # make sure the frame that called up this dialog ends up in front once the dialog is gone
    # otherwise in Windows the top-level frame ends up in front instead
    SELF.parent.Parent.Raise()


def on_add_file_button(SELF, text):
    dlg = wx.FileDialog(
        None, message=text,
        defaultDir=os.getcwd(),
        defaultFile="",
        style=wx.FD_OPEN | wx.FD_CHANGE_DIR
    )
    if dlg.ShowModal() == wx.ID_OK:
        SELF.file_path.SetValue(str(dlg.GetPath()))
    # make sure the frame that called up this dialog ends up in front once the dialog is gone
    # otherwise in Windows the top-level frame ends up in front instead
    SELF.parent.Parent.Raise()



class UpgradeDialog(wx.Dialog):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """
        Dialog for MagIC 2 --> MagIC 3 upgrade warning
        """
        wx.Dialog.__init__(self, parent, title="Warning")

        msg = """This tool is meant for relatively simple upgrades
(for instance, a measurement file, a sample file, and a criteria file).
If you have a more complex contribution to upgrade, and you want maximum accuracy,
use the upgrade tool at https://www2.earthref.org/MagIC/upgrade.

What do you want to do?"""

        txt = wx.StaticText(self, label=msg)
        txt_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Warning")
        txt_sizer.Add(txt, flag=wx.ALL|wx.ALIGN_CENTER, border=5)

        btn_boxSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnOk = wx.Button(self, wx.ID_OK, label="Continue with local upgrade")
        btnCancel = wx.Button(self, wx.ID_CANCEL, label="Open earthref upgrade tool")

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(btnOk)
        btnSizer.AddButton(btnCancel)
        btnSizer.Realize()

        main_boxSizer = wx.BoxSizer(wx.VERTICAL)
        main_boxSizer.Add(txt_sizer, flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        main_boxSizer.Add(btnSizer)
        self.SetSizer(main_boxSizer)
        self.Fit()


def simple_warning(text=None):
    if not text:
        text = "Something went wrong\nSee warnings in Terminal/Command Prompt and try again\nMake sure you have filled out all required fields"
    dlg = wx.MessageDialog(None, message=text, caption="warning", style=wx.ICON_ERROR|wx.OK)
    dlg.ShowModal()
    dlg.Destroy()

def warning_with_override(text):
    dlg = wx.MessageDialog(None, message=text, caption="warning", style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_ERROR)
    result = dlg.ShowModal()
    dlg.Destroy()
    return result


def on_helpButton(command=None, text=None):
    import subprocess
    if text:
        result = text
    else:
        result = subprocess.check_output(command, shell=True)
    dlg = wx.Dialog(None, title="help")
    text = wx.TextCtrl(dlg, -1, result, size=(620, 540), style=wx.TE_MULTILINE | wx.TE_READONLY)
    sizer = wx.BoxSizer(wx.VERTICAL)
    btnsizer = wx.BoxSizer()
    btn = wx.Button(dlg, wx.ID_OK)
    btnsizer.Add(btn, 0, wx.ALL, 5)
    btnsizer.Add((5, -1), 0, wx.ALL, 5)
    sizer.Add(text, 0, wx.EXPAND|wx.ALL, 5)
    sizer.Add(btnsizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    dlg.SetSizerAndFit(sizer)
    dlg.Centre()
    dlg.ShowModal()
    dlg.Destroy()


def run_command(SELF, command, outfile):
    print("-I- Running Python command:\n %s"%command)
    os.system(command)
    print("-I- Saved results in MagIC format file: {}".format(outfile))


def run_command_and_close_window(SELF, command, outfile):
    print("-I- Running Python command:\n %s"%command)
    os.system(command)
    if not outfile:
        outfile = ''
    msg = "file(s) converted to MagIC format file:\n%s.\n\nSee Terminal/message window for errors"% outfile
    dlg = wx.MessageDialog(None, caption="Message:", message=msg, style=wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()
    SELF.Destroy()
    SELF.Parent.Raise()

def close_window(SELF, command, outfile):
    print("-I- Finished running equivalent to Python command:\n %s"%command)
    if not outfile:
        outfile = ''
    msg = "file(s) converted to MagIC format file:\n%s.\n\nSee Terminal/message windowfor errors"% outfile
    dlg = wx.MessageDialog(None, caption="Message:", message=msg, style=wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()
    SELF.Destroy()
    SELF.Parent.Raise()

# menu events

def on_cookbook(event):
    webbrowser.open("http://earthref.org/PmagPy/cookbook/", new=2)

def on_git(event):
    webbrowser.open("https://github.com/ltauxe/PmagPy", new=2)

def on_show_output(event):
    outframe = get_output_frame()
    outframe.Show()
    outframe.Raise()

def on_hide_output(event):
    outframe = get_output_frame()
    outframe.Hide()

def get_output_frame():
    print('-I- Fetching output frame')
    wins = wx.GetTopLevelWindows()
    for win in wins:
        if win.Name == 'frame':
            return win
    return False

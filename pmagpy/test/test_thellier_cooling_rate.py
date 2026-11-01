"""Cooling-rate descriptions must refer to their own measurements (#987)."""

import copy
import io
from pathlib import Path
from types import MethodType, SimpleNamespace

import numpy as np
import pytest

from dialogs import thellier_gui_lib


@pytest.fixture
def cooling_records():
    # Measured values shipped in data_files/generic_magic/CR/generic_CR.magic.
    return [
        dict(magic_method_codes='LP-CR-TRM:LT-T-I',
             measurement_description='cooling_rate:43.6:K/min',
             measurement_magn_moment='3.02e-7'),
        dict(magic_method_codes='LP-CR-TRM:LT-T-I',
             measurement_description='cooling_rate:1.3:K/min',
             measurement_magn_moment='3.29e-7'),
        dict(magic_method_codes='LP-CR-TRM:LT-PTRM-I',
             measurement_description='cooling_rate:43.6:K/min',
             measurement_magn_moment='3.03e-7'),
    ]


def test_measured_cooling_rates(cooling_records):
    actual = thellier_gui_lib.get_cooling_rate_data(cooling_records)
    assert actual['pairs'] == [[43.6, 3.02e-7], [1.3, 3.29e-7]]
    assert actual['alteration_check'] == [43.6, 3.03e-7]
    assert actual['lab_cooling_rate'] == 43.6


@pytest.mark.parametrize('index', [0, 1, 2])
@pytest.mark.parametrize('description', ['slow', '', 'cooling_rate:fast:K/min', None])
def test_incomplete_cooling_rates_are_not_reused(cooling_records, index, description):
    cooling_records[index]['measurement_description'] = description
    assert thellier_gui_lib.get_cooling_rate_data(cooling_records) is None


@pytest.mark.parametrize('description', ['slow', 'K/min:43.6', 'cooling_rate:0:K/min',
                                         'cooling_rate:-1:K/min', 'cooling_rate:nan:K/min',
                                         'cooling_rate:inf:K/min'])
def test_unusable_extra_measurement_is_ignored(cooling_records, description):
    extra = dict(cooling_records[0], measurement_description=description,
                 measurement_magn_moment='1.0')
    expected = thellier_gui_lib.get_cooling_rate_data(cooling_records)
    assert thellier_gui_lib.get_cooling_rate_data([extra] + cooling_records + [extra]) == expected


def test_baseline_does_not_need_a_cooling_rate(cooling_records):
    baseline = dict(magic_method_codes='LP-CR-TRM:LT-T-Z',
                    measurement_description='baseline', measurement_magn_moment='1e-9')
    actual = thellier_gui_lib.get_cooling_rate_data([baseline] + cooling_records)
    assert actual['baseline'] == 1e-9
    assert actual['pairs'] == [[43.6, 3.02e-7], [1.3, 3.29e-7]]


def test_two_distinct_in_field_rates_are_needed(cooling_records):
    cooling_records[1]['measurement_description'] = 'cooling_rate:43.6:K/min'
    assert thellier_gui_lib.get_cooling_rate_data(cooling_records) is None


@pytest.fixture
def load_measured_specimen(tmp_path):
    # The data path can be tested without starting a wx application. CI without
    # wxPython still exercises the parsing tests above.
    pytest.importorskip('wx')
    from programs import thellier_gui
    from pmagpy import pmag
    from pmagpy.mapping import map_magic
    import pandas as pd

    root = Path(pmag.__file__).resolve().parents[1]
    records, _ = pmag.magic_read(str(root / 'data_files/3_0/Megiddo/measurements.txt'))
    selected = [r for r in records if r['specimen'] == 'mgf10a01']
    # The shipped specimens and samples tables give this hierarchy and the
    # ancient cooling rate 4.38e11 K/My for mgf10a.
    for rec in selected:
        rec.update(sample='mgf10a', site='mgf10')
    records = map_magic.convert_meas_df_thellier_gui(
        pd.DataFrame(selected), output=2).to_dict('records')

    def load(change=None):
        measurements = copy.deepcopy(records)
        if change:
            change(measurements)
        filename = str(tmp_path / 'magic_measurements.txt')
        pmag.magic_write(filename, measurements, 'magic_measurements')
        frame = SimpleNamespace(
            WD=str(tmp_path), MagIC_directories_list=[], data_model=2,
            magic_file=filename, GUI_log=io.StringIO(),
            Data_info={'er_samples': {'mgf10a': {'sample_cooling_rate': '4.38e11'}}})
        frame.sortarai = MethodType(thellier_gui.Arai_GUI.sortarai, frame)
        data, _ = thellier_gui.Arai_GUI.get_data(frame)
        return data['mgf10a01'], frame.GUI_log.getvalue()

    return load


@pytest.mark.parametrize('index', [0, 1, 2])
def test_loader_keeps_other_measurements_when_cooling_rate_is_missing(load_measured_specimen, index):
    control, _ = load_measured_specimen()

    def remove_rate(records):
        cooling = [r for r in records if 'LP-CR-TRM' in r['magic_method_codes']]
        cooling[index]['measurement_description'] = 'slow'

    actual, log = load_measured_specimen(remove_rate)
    assert 'cooling_rate_data' not in actual
    assert 'Skipping cooling rate correction for specimen mgf10a01' in log
    for key in ['x_Arai', 'y_Arai', 't_Arai', 'zdata', 'PTRMS', 'NRMS']:
        np.testing.assert_array_equal(actual[key], control[key])


@pytest.mark.parametrize('position', [0, -1])
def test_loader_uses_only_measured_rates_in_the_fit(load_measured_specimen, position):
    control, _ = load_measured_specimen()

    def add_unrated_measurement(records):
        extra = dict(next(r for r in records if 'LP-CR-TRM' in r['magic_method_codes']))
        extra.update(measurement_description='slow', measurement_magn_moment='1.0')
        records.insert(position, extra)

    actual, _ = load_measured_specimen(add_unrated_measurement)
    result = actual['cooling_rate_data']
    # Independent two-rate regression: at ln(43.6/r)=0 the mean of the two
    # fast moments is 3.025e-7, so normalized intercept is 1; the slow point
    # determines the slope. This gives the extrapolated ancient correction.
    slope = (3.29e-7 / 3.025e-7 - 1) / np.log(43.6 / 1.3)
    expected = 1 / (1 + slope * np.log(43.6 / (4.38e11 / (1e6*365*24*60))))
    assert result['CR_correction_factor'] == pytest.approx(expected, rel=1e-14)
    assert result['CR_correction_factor'] == control['cooling_rate_data']['CR_correction_factor']
    for key in ['pairs', 'alteration_check', 'moment_norm', 'polyfit']:
        np.testing.assert_array_equal(result[key], control['cooling_rate_data'][key])

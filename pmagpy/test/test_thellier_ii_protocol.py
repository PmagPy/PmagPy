"""Thellier-II codes on in-field rows must restore the demagnetization path."""

import copy
import io
from types import MethodType, SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from pmagpy import pmag
from pmagpy.mapping import map_magic


@pytest.fixture
def load_experiment(tmp_path):
    pytest.importorskip('wx')
    from programs import thellier_gui
    from pmagpy import contribution_builder as cb

    def load(records, data_model):
        filename = str(tmp_path / 'magic_measurements.txt')
        frame = SimpleNamespace(
            WD=str(tmp_path), MagIC_directories_list=[], data_model=data_model,
            magic_file=filename, GUI_log=io.StringIO(),
            Data_info={'er_samples': {}}, user_warning=pytest.fail)
        if data_model == 3:
            converted = map_magic.convert_meas_df_thellier_gui(
                pd.DataFrame(records), output=3)
            frame.contribution = cb.Contribution(str(tmp_path), read_tables=[])
            frame.contribution.add_magic_table('measurements', df=converted)
        else:
            pmag.magic_write(filename, records, 'magic_measurements')
        frame.sortarai = MethodType(thellier_gui.Arai_GUI.sortarai, frame)
        data, _ = thellier_gui.Arai_GUI.get_data(frame)
        return data['specimen']

    return load


def experiment(protocol, microwave=False, zero_field=False):
    """Make pairs M+ = NRM + pTRM and M- = NRM - pTRM."""
    parent = 'LP-PI-M' if microwave else 'LP-PI-TRM'
    treatment = 'LT-M' if microwave else 'LT-T'
    nrm = np.array([1., 0.5, 0.8])
    vectors = [nrm]
    records = []

    def record(temp, vector, method, theta):
        moment = np.linalg.norm(vector)
        dec = np.degrees(np.arctan2(vector[1], vector[0])) % 360
        inc = np.degrees(np.arcsin(vector[2] / moment))
        rec = dict(
            er_specimen_name='specimen', er_sample_name='sample',
            er_site_name='site', er_location_name='location',
            magic_method_codes=parent + ':' + method,
            measurement_number=str(len(records)),
            magic_instrument_codes='instrument',
            measurement_dec=dec, measurement_inc=inc,
            measurement_magn_moment=moment, measurement_flag='g',
            measurement_description='Step Number-%s' % temp,
            treatment_temp=temp, treatment_dc_field=4e-5,
            treatment_dc_field_phi=0., treatment_dc_field_theta=theta)
        if microwave:
            rec['treat_mw_step'] = temp
        records.append(rec)

    record(0 if microwave else 273, nrm, 'LT-NO', 90.)
    for index, fraction in enumerate([0.8, 0.55, 0.3], start=1):
        temp = index if microwave else 273 + index * 100
        remaining = fraction * nrm
        acquired = np.array([0.06, 0.08, 0.3]) * index
        vectors.append(remaining)
        if zero_field:
            record(temp, remaining, treatment + '-Z', 0.)
        else:
            record(temp, remaining - acquired, treatment + '-I', -90.)
        record(temp, remaining + acquired, treatment + '-I', 90.)
    for rec in records[1:]:
        rec['magic_method_codes'] += ':' + protocol
    return records, np.array(vectors) / np.linalg.norm(nrm)


@pytest.mark.parametrize('data_model', [2, 3])
@pytest.mark.parametrize('protocol,microwave', [
    ('LP-PI-II', False), ('LP-PI-T-II', False), ('LP-PI-M-II', True)])
def test_in_field_protocol_codes_restore_all_vectors(load_experiment, data_model,
                                                    protocol, microwave):
    records, expected = experiment(protocol, microwave)
    actual = load_experiment(copy.deepcopy(records), data_model)
    assert len(actual['z_temp']) == 4
    np.testing.assert_allclose(actual['zdata'], expected, atol=1e-14)
    expected_diffs = np.linalg.norm(np.diff(expected, axis=0), axis=1)
    expected_vds = expected_diffs.sum() + np.linalg.norm(expected[-1])
    assert actual['vds'] == pytest.approx(expected_vds)
    np.testing.assert_allclose(actual['y_Arai'], [1., 0.8, 0.55, 0.3])

    # Keeping the experiment code on NRM remains compatible.
    records[0]['magic_method_codes'] += ':' + protocol
    control = load_experiment(records, data_model)
    for key in ['zdata', 'zij_rotated', 'x_Arai', 'y_Arai', 'vector_diffs']:
        np.testing.assert_array_equal(actual[key], control[key])


@pytest.mark.parametrize('data_model', [2, 3])
def test_other_protocols_keep_the_measured_zero_field_block(load_experiment, data_model):
    # The extra suffix is deliberately not the II method code. An ordinary
    # ZI experiment must retain its flags and instrument metadata.
    records, expected = experiment('LP-PI-TRM-ZI', zero_field=True)
    records[0]['magic_method_codes'] += ':LP-PI-II-unrelated'
    actual = load_experiment(records, data_model)
    np.testing.assert_allclose(actual['zdata'], expected, atol=1e-14)
    assert [row[4] for row in actual['zijdblock']] == [1, 1, 1, 1]
    assert [row[6] for row in actual['zijdblock']] == ['instrument'] * 4

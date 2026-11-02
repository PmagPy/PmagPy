"""Measurement-level AMS selection must retain treatment observations."""
import numpy as np
import pandas as pd
import pytest
from pmagpy import contribution_builder as cb, ipmag


@pytest.fixture
def contribution(tmp_path):
    con = cb.Contribution(str(tmp_path), read_tables=[])
    rows = []
    for i in range(3):
        for step, field in enumerate([0.01, 0.05]):
            rows.append(dict(measurement=f"m{i}-{step}", specimen=f"sp{i}",
                             experiment=f"sp{i}:AMS", method_codes="LP-AN-MS:LT-AF-Z-X",
                             treat_ac_field=str(field), treat_step_num=step+i,
                             aniso_type="AMS", aniso_tilt_correction=-1,
                             aniso_s=f"{.37+i*.001}:{.33-step*.001}:{.30-i*.001+step*.001}:0.001:0.002:0.003"))
    con.add_magic_table_from_data('measurements', data=rows)
    con.add_magic_table_from_data('specimens', data=[
        dict(specimen=f"sp{i}", sample=f"sa{i}") for i in range(3)])
    con.add_magic_table_from_data('samples', data=[
        dict(sample=f"sa{i}", site="site"+str(i//2)) for i in range(3)])
    con.add_magic_table_from_data('sites', data=[
        dict(site="site0", location="location"), dict(site="site1", location="location")])
    return con


@pytest.fixture
def captured(monkeypatch):
    frames = []
    def record(fignum, frame, **kwargs):
        frames.append((frame.copy(), kwargs))
        return {}
    monkeypatch.setattr(ipmag, 'plot_aniso', record)
    return frames


def run(con, **kwargs):
    return ipmag.aniso_magic(contribution=con, source='measurements',
                             save_plots=False, verbose=False, **kwargs)


def test_step_selection_preserves_measurement_ids_hierarchy_and_input(contribution, captured):
    before = contribution.tables['measurements'].df.copy(deep=True)
    assert run(contribution, treatments={'treat_ac_field': '5e-2'})[0]
    frame, _ = captured[0]
    assert list(frame.measurement) == ['m0-1', 'm1-1', 'm2-1']
    assert list(frame.site) == ['site0', 'site0', 'site1']
    assert set(frame.location) == {'location'}
    pd.testing.assert_frame_equal(contribution.tables['measurements'].df[before.columns], before)


def test_experiment_names_may_contain_colons(contribution, captured):
    run(contribution, experiments=['sp1:AMS'], treatments={'treat_ac_field': .01})
    assert list(captured[0][0].measurement) == ['m1-0']


def test_method_codes_match_tokens_and_require_all(contribution, captured):
    run(contribution, method_codes='LP-AN-MS:LT-AF-Z-X', plot_mean=False)
    assert len(captured[0][0]) == 6
    captured.clear()
    assert run(contribution, method_codes='LT-AF-Z', plot_mean=False) == (False, [])
    assert not captured


def test_missing_selection_returns_image_record_shape(contribution, captured):
    assert run(contribution, experiments='absent', image_records=True) == (False, [], [])
    assert not captured


@pytest.mark.parametrize('kwargs', [dict(), dict(experiments='sp0:AMS')])
def test_mixed_steps_are_not_averaged(contribution, captured, kwargs):
    with pytest.raises(ValueError, match='different treat_ac_field'):
        run(contribution, **kwargs)
    assert not captured


def test_site_filter_is_applied_before_mean_condition_check(contribution, captured):
    df = contribution.tables['measurements'].df
    df.loc[df.specimen == 'sp2', 'treat_ac_field'] = '.05'
    run(contribution, sites='site1')
    assert list(captured[0][0].specimen) == ['sp2', 'sp2']


def test_individual_axes_keep_repeated_specimens(contribution, captured):
    run(contribution, plot_mean=False)
    frame, options = captured[0]
    assert len(frame) == 6
    assert list(frame.specimen) == ['sp0', 'sp0', 'sp1', 'sp1', 'sp2', 'sp2']
    assert options['plot_mean'] is False


@pytest.mark.parametrize('kwargs,match', [
    (dict(source='bad'), 'source must'),
    (dict(source='specimens', treatments={}), 'require source'),
    (dict(treatments={'typo': 1}), 'unknown treatment'),
    (dict(treatments={'treat_ac_field': np.nan}), 'finite numbers'),
    (dict(method_codes=''), 'non-empty'),
])
def test_invalid_selection_is_explicit(contribution, kwargs, match):
    opts = dict(contribution=contribution, source='measurements', save_plots=False)
    opts.update(kwargs)
    with pytest.raises(ValueError, match=match):
        ipmag.aniso_magic(**opts)


def test_missing_source_and_missing_tensor_return_shape(tmp_path):
    con = cb.Contribution(str(tmp_path), read_tables=[])
    assert run(con, image_records=True) == (False, [], [])
    con.add_magic_table_from_data('measurements', data=[dict(measurement='m', specimen='sp')])
    assert run(con) == (False, [])


def test_custom_measurement_filename(contribution, tmp_path, captured):
    for table in contribution.tables.values():
        table.write_magic_file(dir_path=str(tmp_path))
    (tmp_path / 'measurements.txt').rename(tmp_path / 'measured_ams.txt')
    assert ipmag.aniso_magic(source='measurements', infile='measured_ams.txt',
                             dir_path=str(tmp_path), save_plots=False,
                             treatments={'treat_ac_field': .05})[0]
    assert list(captured[0][0].measurement) == ['m0-1', 'm1-1', 'm2-1']


def test_single_tensor_can_plot_individual_axes():
    frame = pd.DataFrame([dict(aniso_s='.4:.33:.27:.001:.002:.003')])
    assert set(ipmag.plot_aniso(1, frame, plot_mean=False)) == {'data'}


def test_successive_steps_save_distinct_plots(contribution):
    names = []
    for field in [.01, .05]:
        ok, saved, records = ipmag.aniso_magic(
            contribution=contribution, source='measurements', image_records=True,
            treatments={'treat_ac_field': field}, save_plots=True)
        assert ok and len(saved) == len(records) == 2
        assert all('treat_ac_field-' + str(field) in rec['file'] for rec in records)
        names.extend(rec['file'] for rec in records)
    assert len(set(names)) == 4


@pytest.mark.parametrize('column,values', [
    ('method_codes', ['LP-AN-MS:LT-AF-Z-X', 'LP-AN-MS:LT-AF-Z-Y']),
    ('aniso_type', ['AMS', 'ATRM']),
    ('treat_temp', [300., np.nan]),
])
def test_mean_condition_includes_method_type_and_missing_values(contribution, column, values):
    df = contribution.tables['measurements'].df
    df[column] = [values[(i//2) % 2] for i in range(6)]
    with pytest.raises(ValueError, match='different ' + column):
        run(contribution, treatments={'treat_ac_field': .05} if column != 'method_codes' else None)


@pytest.mark.parametrize('column,kwargs', [
    ('experiment', {'experiments': 'sp0:AMS'}),
    ('method_codes', {'method_codes': 'LP-AN-MS'}),
])
def test_missing_filter_column_is_explicit(contribution, column, kwargs):
    contribution.tables['measurements'].df = contribution.tables['measurements'].df.drop(columns=[column])
    with pytest.raises(ValueError, match='selection requires'):
        run(contribution, **kwargs)


def test_single_measurement_has_one_axes_plot(contribution):
    ok, saved, records = ipmag.aniso_magic(
        contribution=contribution, source='measurements', image_records=True,
        experiments='sp0:AMS', treatments={'treat_ac_field': .05},
        plot_mean=False, save_plots=True)
    assert ok and len(saved) == len(records) == 1

"""
Tests for ipmag.dmag_magic and ipmag.select_demag_records.

Regression tests for PmagPy/PmagPy#572: dmag_magic selected records by lab
treatment alone, so the 180 mT ARM steps of anisotropy-of-ARM experiments
(LT-AF-Z:LP-AN-ARM) were plotted alongside the LP-DIR-AF demagnetization
data and drew a vertical line of points at 180 mT.
"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from pmagpy import contribution_builder as cb
from pmagpy import ipmag

DATA_FILES = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'data_files')


def measurements(dataset):
    con = cb.Contribution(os.path.join(DATA_FILES, dataset),
                          single_file='measurements.txt')
    return con.tables['measurements']


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


class TestSelectDemagRecords:

    def test_lp_dir_records_preferred_over_arm_anisotropy(self):
        # data_files/dmag_magic: 978 LT-AF-Z records, 950 of them LP-DIR-AF and
        # 28 of them LT-AF-Z:LP-AN-ARM (three specimens, all at 0.18 T)
        table = measurements('dmag_magic')
        data = ipmag.select_demag_records(table, 'LT-AF-Z')
        assert len(data) == 950
        assert not data.method_codes.str.contains('LP-AN-ARM').any()
        assert data.method_codes.str.contains('LP-DIR-AF').all()
        # the ARM experiments put ten measurements per specimen at 0.18 T,
        # which is what drew the vertical line of points at 180 mT; the
        # remaining LP-DIR-AF data have at most replicate (<= 3) measurements
        # at a step
        before = table.get_records_for_code('LT-AF-Z')
        per_step = lambda df: df.groupby(['specimen', 'treat_ac_field']).size().max()
        assert per_step(before) == 10
        assert per_step(data) <= 3

    def test_thermal_zero_field_steps_of_paleointensity_dropped(self):
        # the same file holds Thellier-type experiments whose zero-field steps
        # are LT-T-Z but not demagnetization experiments
        data = ipmag.select_demag_records(measurements('dmag_magic'), 'LT-T-Z')
        assert len(data) == 432
        assert not data.method_codes.str.contains('LP-PI').any()
        assert data.method_codes.str.contains('LP-DIR-T').all()

    def test_falls_back_when_no_lp_dir_codes(self):
        # data_files/zeq_magic thermal data carry LT-T-Z only; all are kept
        table = measurements('zeq_magic')
        data = ipmag.select_demag_records(table, 'LT-T-Z')
        assert len(data) == 47
        assert not data.method_codes.str.contains('LP-DIR').any()

    def test_xlp_accepts_string_list_and_colon_delimited(self):
        table = measurements('dmag_magic')
        base = ipmag.select_demag_records(table, 'LT-T-Z')
        for xlp in ('LP-DIR-T', ['LP-DIR-T'], 'LP-DIR-T:LP-PI'):
            assert len(ipmag.select_demag_records(table, 'LT-T-Z', xlp)) == 0
        # excluding a protocol that is not present changes nothing
        assert len(ipmag.select_demag_records(table, 'LT-T-Z', ['LP-AN'])) == len(base)
        assert len(ipmag.select_demag_records(table, 'LT-T-Z', '')) == len(base)

    def test_xlp_still_applies_without_lp_dir_codes(self):
        # ani_depthplot thermal data are LT-T-Z with LP-IRM-3D (Lowrie test);
        # nothing has LP-DIR, so all 768 are kept unless excluded explicitly
        table = measurements('ani_depthplot')
        assert len(ipmag.select_demag_records(table, 'LT-T-Z')) == 768
        assert len(ipmag.select_demag_records(table, 'LT-T-Z', 'LP-IRM')) == 0


class TestDmagMagic:

    def test_af_plot_saved_and_returned(self, tmp_path):
        ok, saved = ipmag.dmag_magic(dir_path=str(tmp_path),
                                     input_dir_path=os.path.join(DATA_FILES, 'dmag_magic'),
                                     LT='AF', fmt='png')
        assert ok is True
        assert len(saved) == 1
        assert os.path.isfile(saved[0])
        assert saved[0].endswith('Jan Mayen_LT-AF-Z.png')

    def test_plot_by_site_respects_n_plots(self, tmp_path):
        ok, saved = ipmag.dmag_magic(dir_path=str(tmp_path),
                                     input_dir_path=os.path.join(DATA_FILES, 'dmag_magic'),
                                     LT='AF', plot_by='sit', n_plots=2, fmt='png')
        assert ok is True
        assert len(saved) == 2
        assert all(os.path.isfile(f) for f in saved)

    def test_xlp_list_accepted_end_to_end(self, tmp_path):
        ok, saved = ipmag.dmag_magic(dir_path=str(tmp_path),
                                     input_dir_path=os.path.join(DATA_FILES, 'dmag_magic'),
                                     LT='T', XLP=['LP-PI', 'LP-AN'], fmt='png')
        assert ok is True
        assert len(saved) == 1

    def test_no_intensity_data_returns_false(self, tmp_path):
        # microwave demag: nothing in the example data
        result = ipmag.dmag_magic(dir_path=str(tmp_path),
                                  input_dir_path=os.path.join(DATA_FILES, 'dmag_magic'),
                                  LT='M', fmt='png')
        assert result == (False, [])

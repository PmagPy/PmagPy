"""
Tests for ipmag.atrm_magic, which fits an anisotropy of thermal remanence
(ATRM) tensor to six in-field steps (+X, +Y, +Z, -X, -Y, -Z) of each specimen.

The example data in data_files/atrm_magic are checked against
atrm_results.txt, the rmag_results table that PmagPy 3.22 (data model 2.5)
wrote for the same specimens, and synthetic experiments are built from a
known tensor.
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag, pmag

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir, 'data_files', 'atrm_magic')

# the six in-field positions of atrm_magic, as (phi, theta) of the lab field
POSITIONS = [(0, 0), (90, 0), (0, 90), (180, 0), (270, 0), (0, -90)]

CHI = np.array([[1.20, 0.05, -0.03],
                [0.05, 1.00, 0.02],
                [-0.03, 0.02, 0.80]]) * 1e-8
# small fixed perturbation of each in-field step, so the Hext sigma is finite
NOISE = 2e-11 * np.array([[1, -2, 1], [-1, 1, 2], [2, 1, -1],
                          [-2, 1, 1], [1, 2, -1], [1, -1, -2]])


# atrm_magic casts the eigenvalues it gets from numpy.linalg.eig to real
pytestmark = pytest.mark.filterwarnings('ignore:Casting complex values to real')


def write_atrm_measurements(path, baseline=(0., 0., 0.), alteration_factor=None):
    """
    Write a synthetic ATRM experiment for one specimen, 'syn01a'.

    Args:
        path (str): file to write the measurements table to
        baseline (sequence of float): x, y, z of the remanence measured after
            the zero-field step, which is also carried by every in-field step
        alteration_factor (float or None): if given, an alteration check
            (LT-PTRM-I) in the +X position, with the +X moment times this factor

    Returns:
        list of float: the magn_moment values as written, in file order
    """
    fields = np.array([pmag.dir2cart([phi, theta, 1.]) for phi, theta in POSITIONS])
    moments = fields @ CHI + NOISE + np.asarray(baseline)
    steps = [('LT-T-Z:LP-AN-TRM', 0, 0, np.asarray(baseline, dtype=float))]
    steps += [('LT-T-I:LP-AN-TRM', phi, theta, moment)
              for (phi, theta), moment in zip(POSITIONS, moments)]
    if alteration_factor is not None:
        steps.append(('LT-PTRM-I:LP-AN-TRM', 0, 0, moments[0] * alteration_factor))
    header = ['specimen', 'sample', 'method_codes', 'treat_dc_field_phi',
              'treat_dc_field_theta', 'dir_dec', 'dir_inc', 'magn_moment']
    written = []
    with open(path, 'w') as f:
        f.write('tab\tmeasurements\n' + '\t'.join(header) + '\n')
        for codes, phi, theta, xyz in steps:
            if not np.any(xyz):
                dec, inc, moment = 0., 0., 0.
            else:
                dec, inc, moment = pmag.cart2dir(xyz)
            written.append(float('%.6e' % moment))
            f.write('\t'.join(['syn01a', 'syn01', codes, str(phi), str(theta),
                               '%.4f' % dec, '%.4f' % inc, '%.6e' % moment]) + '\n')
    return written


def run_atrm(work_dir, meas_file='measurements.txt', **kwargs):
    """Run atrm_magic in work_dir and return the output specimens table."""
    ipmag.atrm_magic(meas_file, dir_path=str(work_dir), input_dir_path=str(work_dir),
                     output_spec_file='atrm_specimens.txt', **kwargs)
    return pd.read_csv(os.path.join(work_dir, 'atrm_specimens.txt'),
                       sep='\t', header=1).set_index('specimen')


def eigen_parameters(value):
    """Split an aniso_v1/v2/v3 string 'tau:dec:inc' into floats."""
    return [float(x) for x in value.split(':')]


@pytest.fixture(scope='module')
def example_results(tmp_path_factory):
    """atrm_magic on the example data, with the input specimens table."""
    work_dir = tmp_path_factory.mktemp('atrm_example')
    for fname in ['atrm_measurements3.txt', 'orig_specimens.txt']:
        shutil.copy(os.path.join(DATA_DIR, fname), work_dir)
    return run_atrm(work_dir, 'atrm_measurements3.txt',
                    input_spec_file='orig_specimens.txt')


@pytest.fixture(scope='module')
def reference_results():
    """The rmag_results table PmagPy 3.22 wrote for the example data."""
    return pd.read_csv(os.path.join(DATA_DIR, 'atrm_results.txt'),
                       sep='\t', header=1).set_index('er_specimen_names')


class TestExampleData:

    def test_every_specimen_has_a_tensor(self, example_results, reference_results):
        """all 30 specimens in the example are fitted, as in the reference"""
        assert sorted(example_results.index) == sorted(reference_results.index)
        assert (example_results['aniso_type'] == 'ATRM').all()
        assert (example_results['aniso_s_n_measurements'] == 6).all()

    def test_eigenvalues_match_reference(self, example_results, reference_results):
        """the normalized eigenvalues agree with PmagPy 3.22 to 1e-6"""
        for specimen, row in example_results.iterrows():
            ref = reference_results.loc[specimen]
            taus = [eigen_parameters(row[col])[0] for col in ('aniso_v1', 'aniso_v2', 'aniso_v3')]
            np.testing.assert_allclose(
                taus, [ref['anisotropy_t1'], ref['anisotropy_t2'], ref['anisotropy_t3']],
                atol=1.5e-6, err_msg=specimen)

    def test_principal_axes_match_reference(self, example_results, reference_results):
        """V1 and V3 are the reference axes (either polarity, to the 0.1 deg rounding)"""
        for specimen, row in example_results.iterrows():
            ref = reference_results.loc[specimen]
            for col, key in (('aniso_v1', 'v1'), ('aniso_v3', 'v3')):
                _, dec, inc = eigen_parameters(row[col])
                axis = pmag.dir2cart([dec, inc, 1.])
                ref_axis = pmag.dir2cart([ref['anisotropy_%s_dec' % key],
                                          ref['anisotropy_%s_inc' % key], 1.])
                angle = np.degrees(np.arccos(min(1., abs(np.dot(axis, ref_axis)))))
                assert angle < 0.2, (specimen, key, angle)

    def test_samples_kept_from_input_specimens(self, example_results):
        """the sample of each specimen comes from the input specimens table"""
        specs = pd.read_csv(os.path.join(DATA_DIR, 'orig_specimens.txt'),
                            sep='\t', header=1).set_index('specimen')
        assert (example_results['sample'] == specs.loc[example_results.index, 'sample']).all()

    def test_f_statistic_matches_reference(self, example_results, reference_results):
        """the Hext F statistic agrees with PmagPy 3.22, which removed the baseline"""
        np.testing.assert_allclose(
            example_results['aniso_ftest'].astype(float),
            reference_results.loc[example_results.index, 'anisotropy_ftest'],
            atol=0.06)


class TestSyntheticExperiment:

    def test_known_tensor_is_recovered(self, tmp_path):
        """the trace-normalized s1..s6 of the tensor used to make the data"""
        write_atrm_measurements(tmp_path / 'measurements.txt')
        spec = run_atrm(tmp_path).loc['syn01a']
        expected = CHI / np.trace(CHI)
        s = np.array(spec['aniso_s'].split(':'), dtype=float)
        np.testing.assert_allclose(
            s, [expected[0, 0], expected[1, 1], expected[2, 2],
                expected[0, 1], expected[1, 2], expected[0, 2]], atol=2e-3)
        assert spec['method_codes'] == 'LP-AN-TRM'

    def test_alteration_check(self, tmp_path):
        """aniso_alt is the percent difference of the check and the +X step"""
        moments = write_atrm_measurements(tmp_path / 'measurements.txt',
                                          alteration_factor=1.04)
        spec = run_atrm(tmp_path).loc['syn01a']
        plus_x, check = moments[1], moments[-1]
        expected = 100 * abs(plus_x - check) / np.mean([plus_x, check])
        assert spec['aniso_alt'] == pytest.approx(expected, abs=0.01)

    def test_alteration_check_with_baseline(self, tmp_path):
        """aniso_alt compares the check and +X step after subtracting the baseline vector"""
        write_atrm_measurements(tmp_path / 'measurements.txt',
                                baseline=(2e-9, -1e-9, 3e-9), alteration_factor=1.04)
        meas = pd.read_csv(tmp_path / 'measurements.txt', sep='\t', header=1)

        def vector(code, phi=0, theta=0):
            row = meas[meas['method_codes'].str.startswith(code)
                       & (meas['treat_dc_field_phi'] == phi)
                       & (meas['treat_dc_field_theta'] == theta)].iloc[0]
            return np.array(pmag.dir2cart([row['dir_dec'], row['dir_inc'], row['magn_moment']]))

        baseline, plus_x, check = vector('LT-T-Z'), vector('LT-T-I'), vector('LT-PTRM-I')
        trm_plus_x = np.linalg.norm(plus_x - baseline)
        trm_check = np.linalg.norm(check - baseline)
        expected = 100 * abs(trm_plus_x - trm_check) / np.mean([trm_plus_x, trm_check])
        raw = 100 * abs(np.linalg.norm(plus_x) - np.linalg.norm(check)) / np.mean(
            [np.linalg.norm(plus_x), np.linalg.norm(check)])
        assert abs(expected - raw) > 0.3  # the baseline matters for this check
        spec = run_atrm(tmp_path).loc['syn01a']
        assert spec['aniso_alt'] == pytest.approx(expected, abs=0.01)

    def test_baseline_does_not_change_sigma(self, tmp_path):
        """a remanence present in every step leaves the fit and its sigma unchanged"""
        clean_dir = tmp_path / 'clean'
        offset_dir = tmp_path / 'offset'
        clean_dir.mkdir()
        offset_dir.mkdir()
        write_atrm_measurements(clean_dir / 'measurements.txt')
        write_atrm_measurements(offset_dir / 'measurements.txt',
                                baseline=(2e-9, -1e-9, 3e-9))
        clean = run_atrm(clean_dir).loc['syn01a']
        offset = run_atrm(offset_dir).loc['syn01a']
        assert float(offset['aniso_s_sigma']) == pytest.approx(
            float(clean['aniso_s_sigma']), rel=0.05)

    def test_missing_baseline_is_reported(self, tmp_path, capsys):
        """without a zero-field step the in-field steps are fit as measured, with a warning"""
        write_atrm_measurements(tmp_path / 'measurements.txt')
        with open(tmp_path / 'measurements.txt') as f:
            lines = [line for line in f if 'LT-T-Z' not in line]
        with open(tmp_path / 'measurements.txt', 'w') as f:
            f.writelines(lines)
        spec = run_atrm(tmp_path).loc['syn01a']
        assert 'no zero-field (LT-T-Z) baseline step' in capsys.readouterr().out
        expected = CHI / np.trace(CHI)
        s = np.array(spec['aniso_s'].split(':'), dtype=float)
        np.testing.assert_allclose(
            s, [expected[0, 0], expected[1, 1], expected[2, 2],
                expected[0, 1], expected[1, 2], expected[0, 2]], atol=2e-3)


def test_measurements_without_atrm_data(tmp_path):
    """a measurements table with no LP-AN-TRM records is reported, not written"""
    with open(tmp_path / 'measurements.txt', 'w') as f:
        f.write('tab\tmeasurements\nspecimen\tmethod_codes\tdir_dec\tdir_inc\tmagn_moment\n')
        f.write('a1\tLT-AF-Z:LP-DIR-AF\t10\t20\t1e-8\n')
    result = ipmag.atrm_magic('measurements.txt', dir_path=str(tmp_path))
    assert result == (False, "No measurement records found with code LP-AN-TRM")
    assert not os.path.exists(tmp_path / 'specimens.txt')


def test_returns_status_and_output_file(tmp_path):
    """the documented return value: (True, output specimens file)"""
    write_atrm_measurements(tmp_path / 'measurements.txt')
    result = ipmag.atrm_magic('measurements.txt', dir_path=str(tmp_path),
                              output_spec_file='out.txt')
    assert result[0] is True
    assert os.path.basename(result[1]) == 'out.txt'


def test_not_a_measurements_file(tmp_path):
    """a table that is not a measurements table gives (False, message)"""
    with open(tmp_path / 'measurements.txt', 'w') as f:
        f.write('tab\tspecimens\nspecimen\tsample\na1\ta\n')
    ran, message = ipmag.atrm_magic('measurements.txt', dir_path=str(tmp_path))
    assert ran is False
    assert 'not a valid measurements file' in message


class TestCommandLine:

    def run_main(self, monkeypatch, work_dir, *args):
        """Run programs/atrm_magic.py main() in work_dir."""
        monkeypatch.chdir(work_dir)
        monkeypatch.setattr('sys.argv', ['atrm_magic.py', *args])
        # imported after sys.argv is set: programs/__init__.py acts on a '-v'
        # in sys.argv (e.g. pytest -v) when it is first imported
        from programs import atrm_magic
        atrm_magic.main()

    def test_writes_specimens_table(self, tmp_path, monkeypatch):
        """the program writes specimens.txt and returns normally"""
        write_atrm_measurements(tmp_path / 'atrm_measurements.txt')
        self.run_main(monkeypatch, tmp_path)
        specs = pd.read_csv(tmp_path / 'specimens.txt', sep='\t', header=1)
        assert list(specs['specimen']) == ['syn01a']

    def test_exits_with_error_without_atrm_data(self, tmp_path, monkeypatch):
        """no LP-AN-TRM records: exit status 1 and no table"""
        with open(tmp_path / 'atrm_measurements.txt', 'w') as f:
            f.write('tab\tmeasurements\nspecimen\tmethod_codes\tdir_dec\tdir_inc\tmagn_moment\n')
            f.write('a1\tLT-AF-Z:LP-DIR-AF\t10\t20\t1e-8\n')
        with pytest.raises(SystemExit) as excinfo:
            self.run_main(monkeypatch, tmp_path)
        assert excinfo.value.code == 1
        assert not os.path.exists(tmp_path / 'specimens.txt')

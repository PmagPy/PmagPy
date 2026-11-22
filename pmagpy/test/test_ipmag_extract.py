"""
Tests for the ipmag functions that make publication tables from MagIC
tables: sites_extract, specimens_extract and criteria_extract (data model 3,
written as Excel or LaTeX) and pmag_results_extract (data model 2.5).

The tests name the output files explicitly (.xlsx or .tex), so they do not
depend on the default file extension.
"""
import os
import re
import shutil

import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir, 'data_files')
MCMURDO = os.path.join(DATA_DIR, '3_0', 'McMurdo')
MEGIDDO = os.path.join(DATA_DIR, '3_0', 'Megiddo')


def read_table(path):
    """Read a MagIC tab-delimited table into a DataFrame."""
    return pd.read_csv(path, sep='\t', header=1)


@pytest.fixture
def openpyxl():
    """Excel output needs openpyxl, which is optional."""
    return pytest.importorskip('openpyxl')


class TestSitesExtract:

    @pytest.fixture
    def mcmurdo_tables(self, tmp_path, openpyxl):
        ok, outfiles = ipmag.sites_extract(
            input_dir_path=MCMURDO, output_dir_path=str(tmp_path),
            directions_file='directions.xlsx', intensity_file='intensity.xlsx',
            info_file='site_info.xlsx')
        assert ok
        assert [os.path.basename(f) for f in outfiles] == [
            'site_info.xlsx', 'intensity.xlsx', 'directions.xlsx']
        return {os.path.basename(f).split('.')[0]: pd.read_excel(f) for f in outfiles}

    def test_directions(self, mcmurdo_tables):
        """one row per site with a direction, with the values of sites.txt"""
        sites = read_table(os.path.join(MCMURDO, 'sites.txt'))
        with_dirs = sites.dropna(subset=['dir_dec', 'dir_inc'])
        directions = mcmurdo_tables['directions'].set_index('Site')
        assert sorted(directions.index) == sorted(with_dirs['site'].unique())
        # the row of a site with a VGP is the one kept
        mc01 = with_dirs[(with_dirs['site'] == 'mc01') & with_dirs['vgp_lat'].notnull()].iloc[0]
        assert directions.loc['mc01', ['Dec.', 'Inc.', 'a95', 'N']].tolist() == pytest.approx(
            [mc01['dir_dec'], mc01['dir_inc'], mc01['dir_alpha95'], mc01['dir_n_samples']])
        assert directions.loc['mc01', ['VGP Lat', 'VGP Long']].tolist() == pytest.approx(
            [mc01['vgp_lat'], mc01['vgp_lon']])

    def test_intensities_in_microtesla(self, mcmurdo_tables):
        """one row per site, with B and its sigma (int_abs in T) in uT"""
        sites = read_table(os.path.join(MCMURDO, 'sites.txt')).dropna(subset=['int_abs'])
        sites = sites.drop_duplicates(subset=['site']).set_index('site')
        intensity = mcmurdo_tables['intensity'].set_index('Site')
        assert sorted(intensity.index) == sorted(sites.index)
        sites = sites.loc[intensity.index]
        # whole microtesla (truncated, at present)
        np.testing.assert_allclose(intensity['B'], 1e6 * sites['int_abs'], atol=1)
        np.testing.assert_allclose(intensity['B sigma'], 1e6 * sites['int_abs_sigma'], atol=1)

    def test_site_information(self, mcmurdo_tables):
        """location, coordinates and age of each site with coordinates"""
        info = mcmurdo_tables['site_info']
        assert list(info.columns) == ['Site', 'Location', 'Lat. (N)', 'Long. (E)',
                                      'Age ', 'Age sigma', 'Units']
        sites = read_table(os.path.join(MCMURDO, 'sites.txt')).dropna(subset=['lat', 'lon'])
        assert set(info['Site']) == set(sites['site'])
        # a site is listed once unless its rows differ (here, in rounding of lat/lon)
        assert not info.duplicated().any()
        assert info.set_index('Site').loc['mc01', ['Lat. (N)', 'Long. (E)', 'Age ']].tolist() == \
            pytest.approx([-77.85, 166.64, 1.18])

    def test_latex(self, tmp_path):
        """LaTeX longtables; a contribution with no intensities gives no intensity file"""
        ok, outfiles = ipmag.sites_extract(
            input_dir_path=MEGIDDO, output_dir_path=str(tmp_path), latex=True,
            directions_file='directions.tex', intensity_file='intensity.tex',
            info_file='site_info.tex')
        assert ok
        assert [os.path.basename(f) for f in outfiles] == ['site_info.tex', 'directions.tex']
        text = open(outfiles[1]).read()
        assert '\\begin{longtable}' in text and '\\end{document}' in text
        n_sites = read_table(os.path.join(MEGIDDO, 'sites.txt')).dropna(
            subset=['dir_dec'])['site'].nunique()
        assert len(re.findall(r'^mg\w+ &', text, flags=re.M)) == n_sites


class TestSpecimensExtract:

    def test_paleointensity_table(self, tmp_path, openpyxl):
        """specimens with int_abs, in uT and degrees C"""
        ok, outfiles = ipmag.specimens_extract(input_dir_path=MCMURDO,
                                               output_dir_path=str(tmp_path),
                                               output_file='specimens.xlsx')
        assert ok
        table = pd.read_excel(outfiles[0]).set_index('specimen')
        specs = read_table(os.path.join(MCMURDO, 'specimens.txt')).dropna(
            subset=['int_abs']).set_index('specimen')
        assert len(table) == len(specs)
        mc01a = specs.loc['mc01a']
        assert table.loc['mc01a', 'B (uT)'] == pytest.approx(1e6 * mc01a['int_abs'], abs=0.05)
        assert table.loc['mc01a', ['Min', 'Max']].tolist() == [
            int(mc01a['meas_step_min'] - 273), int(mc01a['meas_step_max'] - 273)]
        assert table.loc['mc01a', 'Units'] == 'C'

    def test_latex(self, tmp_path):
        ok, outfiles = ipmag.specimens_extract(input_dir_path=MEGIDDO,
                                               output_dir_path=str(tmp_path),
                                               output_file='specimens.tex', latex=True,
                                               longtable=True)
        assert ok
        text = open(outfiles[0]).read()
        n_specs = len(read_table(os.path.join(MEGIDDO, 'specimens.txt')).dropna(
            subset=['int_abs']))
        assert '\\begin{longtable}' in text
        assert len(re.findall(r'^\w+ & \w+ & \d+ & \d+ & C &', text, flags=re.M)) == n_specs


class TestCriteriaExtract:

    def test_criteria_table(self, tmp_path, openpyxl):
        """each criterion split into table and statistic, with its threshold"""
        ok, outfiles = ipmag.criteria_extract(input_dir_path=MEGIDDO,
                                              output_dir_path=str(tmp_path),
                                              output_file='criteria.xlsx')
        assert ok
        table = pd.read_excel(outfiles[0])
        crit = read_table(os.path.join(MEGIDDO, 'criteria.txt'))
        assert list(table.columns) == ['Table', 'Statistic', 'Threshold', 'Operation']
        assert (table['Table'] + '.' + table['Statistic']).tolist() == crit['table_column'].tolist()
        assert table['Operation'].tolist() == crit['criterion_operation'].tolist()
        assert float(table.loc[table['Statistic'] == 'int_frac', 'Threshold'].item()) == 0.7


@pytest.mark.xfail(strict=True, reason=(
    "the header strings are raw strings, so '\\n' is written as a backslash and "
    "an n, e.g. \\documentclass{article}\\n\\usepackage{booktabs}, which LaTeX "
    "stops on as an undefined control sequence"))
@pytest.mark.parametrize('function, kwargs', [
    (ipmag.sites_extract, {'directions_file': 'directions.tex', 'info_file': 'info.tex'}),
    (ipmag.specimens_extract, {'output_file': 'specimens.tex'}),
    (ipmag.criteria_extract, {'output_file': 'criteria.tex'}),
], ids=['sites', 'specimens', 'criteria'])
def test_latex_has_no_literal_newlines(tmp_path, function, kwargs):
    """the LaTeX documents have line breaks, not the two characters '\\n'"""
    ok, outfiles = function(input_dir_path=MEGIDDO, output_dir_path=str(tmp_path),
                            latex=True, **kwargs)
    assert ok
    for fname in outfiles:
        assert not re.search(r'\\n(?![a-z])|\\n\\', open(fname).read()), fname


@pytest.mark.xfail(strict=True, raises=FileNotFoundError, reason=(
    "the try/except IOError is around pmag.resolve_file_name, which does not "
    "open the file; pd.read_csv then raises FileNotFoundError"))
@pytest.mark.parametrize('function, message', [
    (ipmag.sites_extract, 'bad site file name'),
    (ipmag.specimens_extract, 'bad specimen file name'),
    (ipmag.criteria_extract, 'bad criteria file name'),
], ids=['sites', 'specimens', 'criteria'])
def test_missing_input_table(tmp_path, function, message):
    """a missing input table is reported as (False, message)"""
    assert function(input_dir_path=str(tmp_path), output_dir_path=str(tmp_path)) == (
        False, message)


class TestPmagResultsExtract:
    """pmag_results_extract, on the data model 2.5 tables in data_files/pmag_results_extract"""

    @pytest.fixture
    def results_dir(self, tmp_path):
        for fname in ['pmag_results.txt', 'pmag_specimens.txt']:
            shutil.copy(os.path.join(DATA_DIR, 'pmag_results_extract', fname), tmp_path)
        return tmp_path

    def test_specimen_intensities(self, results_dir):
        """one row per specimen with an intensity, in uT"""
        ipmag.pmag_results_extract(WD=str(results_dir), spec_file='pmag_specimens.txt')
        rows = [line.split(' \t ') for line in
                open(results_dir / 'Specimens.txt').read().splitlines()]
        header, rows = rows[0], rows[1:]
        specs = read_table(results_dir / 'pmag_specimens.txt')
        specs = specs[specs['specimen_int'].notnull()].set_index('er_specimen_name')
        table = {row[1]: row for row in rows}
        assert set(table) <= set(specs.index)
        b_col = header.index('B (uT)')
        sr01a1 = specs.loc['sr01a1']
        sr01a1 = sr01a1.iloc[0] if isinstance(sr01a1, pd.DataFrame) else sr01a1
        assert float(table['sr01a1'][b_col]) == pytest.approx(1e6 * sr01a1['specimen_int'], abs=0.05)

    @pytest.mark.xfail(strict=True, reason=(
        "SiteNfo has a Location column, but the rows are written without the "
        "location, so latitude falls under Location"))
    def test_site_info_rows_fill_the_header(self, results_dir):
        ipmag.pmag_results_extract(WD=str(results_dir))
        lines = open(results_dir / 'SiteNfo.txt').read().splitlines()
        n_columns = len(lines[0].split(' \t '))
        assert all(len(line.split(' \t ')) == n_columns for line in lines[1:])

    def test_latex(self, results_dir):
        ok, outfiles = ipmag.pmag_results_extract(WD=str(results_dir), latex=True)
        assert ok
        assert [os.path.basename(f) for f in outfiles] == [
            'Directions.tex', 'Intensities.tex', 'SiteNfo.tex']
        text = open(results_dir / 'Directions.tex').read()
        assert '\\begin{longtable}' in text
        # not anchored to the line start: see test_latex_has_no_literal_newlines
        assert len(re.findall(r'sr\d+ & ', text)) == 21

    @pytest.mark.xfail(strict=True, reason=(
        "the row separators are raw strings, so '\\hline\\n' is written with a "
        "backslash and an n, which LaTeX stops on as an undefined control sequence"))
    def test_latex_has_no_literal_newlines(self, results_dir):
        ok, outfiles = ipmag.pmag_results_extract(WD=str(results_dir), latex=True)
        for fname in outfiles:
            assert not re.search(r'\\n(?![a-z])|\\n\\', open(fname).read()), fname

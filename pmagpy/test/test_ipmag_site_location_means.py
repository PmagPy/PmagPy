"""
Tests for ipmag.site_means_magic and ipmag.location_means_magic: the averaging
of the specimen directions of a specimens table into site means, and of site
means into location means and poles, written into the MagIC tables.
"""
import os

import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag
from pmagpy import pmag
from pmagpy import contribution_builder as cb

WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


def write(directory, table, rows):
    cb.MagicDataFrame(dtype=table, df=pd.DataFrame(rows)).write_magic_file(
        custom_name=os.path.join(str(directory), table + '.txt'), dir_path=str(directory))


def read(directory, table):
    return pd.read_csv(os.path.join(str(directory), table + '.txt'), sep='\t', header=1, dtype=str,
                       keep_default_na=False)


def fisher(directions):
    """an independent Fisher mean: (dec, inc, alpha95, k)"""
    x = np.array([pmag.dir2cart([d, i, 1.]) for d, i in directions])
    r = np.linalg.norm(x.sum(axis=0))
    n = len(x)
    dec, inc, _ = pmag.cart2dir(x.sum(axis=0))
    k = (n - 1) / (n - r)
    a95 = np.degrees(np.arccos(1 - (n - r) / r * (20 ** (1 / (n - 1)) - 1)))
    return dec, inc, a95, k


LINES = [(10., 50.), (20., 55.), (15., 45.)]


@pytest.fixture
def study(tmp_path):
    specimens = []
    for k, (dec, inc) in enumerate(LINES):
        for tilt, shift in (('0', 0.), ('100', 5.)):
            specimens.append({'specimen': 'S1-{}a'.format(k + 1), 'sample': 'S1-{}'.format(k + 1), 'dir_comp': 'ChRM',
                              'dir_dec': dec + shift, 'dir_inc': inc, 'dir_tilt_correction': tilt,
                              'method_codes': 'LP-DIR-AF:DE-BFL:DA-DIR-GEO', 'result_quality': 'g'})
    # a bad specimen, an intensity result and a specimen-coordinate row: not averaged
    specimens.append({'specimen': 'S1-4a', 'sample': 'S1-4', 'dir_comp': 'ChRM', 'dir_dec': 200., 'dir_inc': -30.,
                      'dir_tilt_correction': '0', 'method_codes': 'LP-DIR-AF:DE-BFL', 'result_quality': 'b'})
    specimens.append({'specimen': 'S1-1a', 'sample': 'S1-1', 'dir_comp': 'ChRM', 'dir_dec': 99., 'dir_inc': 9.,
                      'dir_tilt_correction': '-1', 'method_codes': 'LP-DIR-AF:DE-BFL', 'result_quality': 'g'})
    # site S2: two lines and a plane; reversed
    for name, dec, inc, code in (('S2-1a', 195., -52., 'DE-BFL'), ('S2-2a', 190., -48., 'DE-BFL'),
                                 ('S2-3a', 100., 10., 'DE-BFP')):
        specimens.append({'specimen': name, 'sample': name[:-1], 'dir_comp': 'ChRM', 'dir_dec': dec, 'dir_inc': inc,
                          'dir_tilt_correction': '0', 'method_codes': 'LP-DIR-T:' + code, 'result_quality': 'g'})
    # site S3: a single plane, which is not a direction
    specimens.append({'specimen': 'S3-1a', 'sample': 'S3-1', 'dir_comp': 'ChRM', 'dir_dec': 30., 'dir_inc': 20.,
                      'dir_tilt_correction': '0', 'method_codes': 'LP-DIR-T:DE-BFP', 'result_quality': 'g'})
    write(tmp_path, 'specimens', specimens)
    samples = sorted({(s['sample'], s['sample'].split('-')[0]) for s in specimens})
    write(tmp_path, 'samples', [{'sample': s, 'site': t} for s, t in samples])
    write(tmp_path, 'sites', [
        {'site': 'S1', 'location': 'Study', 'lat': 45., 'lon': 10., 'age': 20, 'age_unit': 'Ma',
         'lithologies': 'Basalt', 'geologic_classes': 'Extrusive', 'method_codes': 'LP-DIR-AF:FS-FD'},
        {'site': 'S1', 'location': 'Study', 'int_abs': 4e-5, 'method_codes': 'LP-PI-TRM'},
        {'site': 'S2', 'location': 'Study', 'lat': 45.5, 'lon': 10.5, 'lithologies': 'Basalt'},
        {'site': 'S3', 'location': 'Study', 'lat': 46., 'lon': 11.}])
    write(tmp_path, 'locations', [{'location': 'Study', 'location_type': 'Region', 'lat_s': 45., 'lat_n': 46.,
                                   'lon_w': 10., 'lon_e': 11., 'lithologies': 'Basalt'}])
    return tmp_path


class TestSiteMeans:
    def test_the_lines_of_a_site_are_averaged(self, study):
        means = ipmag.site_means_magic(dir_path=str(study))
        s1 = means[(means['site'] == 'S1') & (means['dir_tilt_correction'] == '0')].iloc[0]
        dec, inc, a95, k = fisher(LINES)
        assert pmag.angle([s1['dir_dec'], s1['dir_inc']], [dec, inc])[0] < 0.1
        assert s1['dir_alpha95'] == pytest.approx(a95, abs=0.1)
        assert s1['dir_k'] == pytest.approx(k, rel=0.01)
        # the bad specimen and the specimen-coordinate row are left out
        assert s1['dir_n_specimens'] == '3' and s1['specimens'] == 'S1-1a:S1-2a:S1-3a'
        assert s1['dir_n_samples'] == '3' and s1['dir_comp_name'] == 'ChRM'
        assert s1['method_codes'] == 'LP-DIR-AF:DE-FM:DE-DI'
        # the VGP of the mean, at the site
        plon, plat, dp, dm = pmag.dia_vgp(s1['dir_dec'], s1['dir_inc'], s1['dir_alpha95'], 45., 10.)
        assert (s1['vgp_lat'], s1['vgp_lon']) == (round(plat, 1), round(plon % 360, 1))
        # tilt-corrected rows give a tilt-corrected mean
        s1_tc = means[(means['site'] == 'S1') & (means['dir_tilt_correction'] == '100')].iloc[0]
        assert pmag.angle([s1_tc['dir_dec'], s1_tc['dir_inc']], fisher([(d + 5, i) for d, i in LINES])[:2])[0] < 0.1

    def test_lines_and_planes(self, study):
        means = ipmag.site_means_magic(dir_path=str(study), write=False)
        s2 = means[means['site'] == 'S2'].iloc[0]
        assert (s2['dir_n_specimens_lines'], s2['dir_n_specimens_planes']) == ('2', '1')
        assert 'DE-FM-LP' in s2['method_codes']
        records = [{'dir_dec': d, 'dir_inc': i, 'dir_type': t} for d, i, t in
                   ((195., -52., 'l'), (190., -48., 'l'), (100., 10., 'p'))]
        lnp = pmag.dolnp(records, 'dir_type')
        assert pmag.angle([s2['dir_dec'], s2['dir_inc']], [float(lnp['dec']), float(lnp['inc'])])[0] < 0.1
        # a single plane has no mean direction
        assert 'S3' not in set(means['site'])

    def test_the_sites_table_keeps_what_it_describes(self, study):
        ipmag.site_means_magic(dir_path=str(study))
        sites = read(study, 'sites')
        s1 = sites[(sites['site'] == 'S1') & (sites['dir_dec'] != '')]
        assert len(s1) == 2                                      # geographic and tilt-corrected
        assert set(s1['lithologies']) == {'Basalt'} and set(s1['age'].astype(float)) == {20.}
        assert set(s1['lat'].astype(float)) == {45.}
        assert all(row.endswith('FS-FD') for row in s1['method_codes'])   # the field codes are kept
        # the intensity result is kept, the row that held no result is replaced
        assert (sites['int_abs'] != '').sum() == 1
        assert len(sites[sites['site'] == 'S1']) == 3
        # the site without a mean keeps its row
        assert len(sites[sites['site'] == 'S3']) == 1
        # averaging again replaces the means, it does not add to them
        ipmag.site_means_magic(dir_path=str(study))
        assert len(read(study, 'sites')) == len(sites)

    def test_options(self, study, tmp_path_factory):
        out = tmp_path_factory.mktemp('out')
        means = ipmag.site_means_magic(dir_path=str(out), input_dir_path=str(study), coords=(0,),
                                       include_bad=True, out_file='site_means.txt')
        s1 = means[means['site'] == 'S1'].iloc[0]
        assert s1['dir_n_specimens'] == '4'                      # with the bad specimen
        assert set(means['dir_tilt_correction']) == {'0'}
        assert os.path.isfile(os.path.join(str(out), 'site_means.txt'))
        assert not ipmag.site_means_magic(dir_path=str(study), components=['other'], write=False).shape[0]


class TestLocationMeans:
    def test_sites_are_averaged_in_a_common_polarity(self, study):
        ipmag.site_means_magic(dir_path=str(study))
        means = ipmag.location_means_magic(dir_path=str(study), coords=(0,))
        row = means.iloc[0]
        sites = read(study, 'sites')
        sites = sites[(sites['dir_dec'] != '') & (sites['dir_tilt_correction'] == '0')].set_index('site')
        s1 = [float(sites.loc['S1', 'dir_dec']), float(sites.loc['S1', 'dir_inc'])]
        s2 = [float(sites.loc['S2', 'dir_dec']), float(sites.loc['S2', 'dir_inc'])]
        # S2 is reversed: its antipode is averaged with S1
        dec, inc, a95, k = fisher([s1, [(s2[0] + 180) % 360, -s2[1]]])
        assert pmag.angle([row['dir_dec'], row['dir_inc']], [dec, inc])[0] < 0.1
        assert row['dir_n_sites'] == '2' and row['sites'] == 'S1:S2'
        assert row['pole_n_sites'] == '2' and row['pole_comp_name'] == 'ChRM'
        assert row['pole_reversed_perc'] == 50.0
        assert 'DE-VGP' in row['method_codes'] and row['description'] == 'ChRM component'
        # the location row keeps its bounds and type
        locations = read(study, 'locations')
        assert len(locations) == 1
        assert locations.iloc[0]['location_type'] == 'Region' and float(locations.iloc[0]['lat_s']) == 45.
        # without the common polarity the two sites nearly cancel
        means = ipmag.location_means_magic(dir_path=str(study), coords=(0,), common_polarity=False, write=False)
        assert means.iloc[0]['dir_alpha95'] > 90 or np.isnan(means.iloc[0]['dir_alpha95'])

    def test_no_site_means(self, study):
        assert not len(ipmag.location_means_magic(dir_path=str(study), write=False))


def test_the_site_means_of_megiddo_are_reproduced(tmp_path):
    # the site means of data_files/3_0/Megiddo, from its specimens table
    src = os.path.join(WD, 'data_files', '3_0', 'Megiddo')
    stored = pd.read_csv(os.path.join(src, 'sites.txt'), sep='\t', header=1)
    stored = stored[stored['dir_dec'].notna()]
    means = ipmag.site_means_magic(dir_path=str(tmp_path), input_dir_path=src, coords=(-1, 0, 100), write=False)
    for _, row in stored.iterrows():
        mine = means[(means['site'] == row['site']) &
                     (means['dir_tilt_correction'] == str(int(row['dir_tilt_correction'])))].iloc[0]
        assert pmag.angle([row['dir_dec'], row['dir_inc']], [mine['dir_dec'], mine['dir_inc']])[0] < 0.1

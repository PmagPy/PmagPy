"""
Regression tests for ipmag.upload_magic.

Guards against a bug where integer "count" columns matching ``*_n*``
(e.g. ``pole_n_sites``, ``dir_n_samples``) were corrupted by
``str.strip('.0')`` — which strips the characters ``.`` and ``0`` from both
ends of the string (so ``'50' -> '5'``, ``'10' -> '1'``, ``'100' -> '1'``)
instead of removing a trailing ``.0`` decimal. The fix removes only a trailing
``.0`` so integer counts are preserved while ``'50.0' -> '50'`` still works.
"""
import os

from pmagpy import ipmag


def _write_table(path, table_type, cols, rows):
    with open(path, 'w') as f:
        f.write('tab delimited\t{}\n'.format(table_type))
        f.write('\t'.join(cols) + '\n')
        for r in rows:
            f.write('\t'.join(str(r[c]) for c in cols) + '\n')


def _parse_tables(path):
    tables = {}
    for block in open(path).read().split('>>>>>>>>>>'):
        lines = [ln for ln in block.split('\n') if ln.strip()]
        if not lines:
            continue
        ttype = lines[0].split('\t')[-1].strip()
        hdr = lines[1].split('\t')
        tables[ttype] = [dict(zip(hdr, ln.split('\t'))) for ln in lines[2:]]
    return tables


class TestUploadMagicCountColumns:
    """Integer count columns must survive upload_magic unchanged."""

    def test_counts_not_corrupted(self, tmp_path):
        d = str(tmp_path)
        site_cols = ['site', 'location', 'method_codes', 'citations',
                     'lat', 'lon', 'dir_tilt_correction',
                     'dir_dec', 'dir_inc', 'dir_n_samples']
        sites = [
            {'site': 'S1', 'location': 'Loc', 'method_codes': 'LP-DIR-T',
             'citations': '10.0000/x', 'lat': '47.0', 'lon': '272.0',
             'dir_tilt_correction': '100', 'dir_dec': '10', 'dir_inc': '5',
             'dir_n_samples': '10'},   # ends in 0 -> was corrupted to '1'
            {'site': 'S2', 'location': 'Loc', 'method_codes': 'LP-DIR-T',
             'citations': '10.0000/x', 'lat': '47.0', 'lon': '272.0',
             'dir_tilt_correction': '100', 'dir_dec': '12', 'dir_inc': '6',
             'dir_n_samples': '6'},
        ]
        _write_table(os.path.join(d, 'sites.txt'), 'sites', site_cols, sites)

        loc_cols = ['location', 'location_type', 'lat_s', 'lat_n',
                    'lon_w', 'lon_e', 'pole_n_sites']
        locs = [{'location': 'Loc', 'location_type': 'Outcrop',
                 'lat_s': '47.0', 'lat_n': '47.5', 'lon_w': '272.0',
                 'lon_e': '272.0', 'pole_n_sites': '50'}]  # was corrupted to '5'
        _write_table(os.path.join(d, 'locations.txt'), 'locations',
                     loc_cols, locs)

        result = ipmag.upload_magic(dir_path=d, input_dir_path=d,
                                    validate=False, verbose=False)
        outfile = result[0]
        assert outfile and os.path.isfile(outfile)

        tables = _parse_tables(outfile)
        assert tables['locations'][0]['pole_n_sites'] == '50'
        # lat_n is a latitude, not a count, and must be left intact
        assert tables['locations'][0]['lat_n'] == '47.5'
        assert sorted(r['dir_n_samples'] for r in tables['sites']) == ['10', '6']

    def test_trailing_decimal_zero_still_stripped(self, tmp_path):
        """A genuine '.0' decimal on a count column is still removed."""
        d = str(tmp_path)
        loc_cols = ['location', 'location_type', 'lat_s', 'lat_n',
                    'lon_w', 'lon_e', 'pole_n_sites']
        locs = [{'location': 'Loc', 'location_type': 'Outcrop',
                 'lat_s': '47.0', 'lat_n': '47.5', 'lon_w': '272.0',
                 'lon_e': '272.0', 'pole_n_sites': '50.0'}]
        _write_table(os.path.join(d, 'locations.txt'), 'locations',
                     loc_cols, locs)
        result = ipmag.upload_magic(dir_path=d, input_dir_path=d,
                                    validate=False, verbose=False)
        tables = _parse_tables(result[0])
        assert tables['locations'][0]['pole_n_sites'] == '50'


class TestValidateMagic:
    """validate_magic downloads through the download functions and re-assembles the contribution offline."""

    EXAMPLE = os.path.join(os.path.dirname(__file__), '..', '..', 'data_files', 'download_magic',
                           'magic_contribution_19340.txt')

    def test_a_private_contribution_goes_through_download_magic_from_id(self, tmp_path, monkeypatch):
        import shutil
        calls = {}

        def fake_download(magic_id, directory='.', share_key=""):
            calls.update(id=magic_id, directory=directory, share_key=share_key)
            shutil.copy(self.EXAMPLE, os.path.join(directory, 'magic_contribution_19340.txt'))
            return True, 'magic_contribution_19340.txt'

        monkeypatch.setattr(ipmag, 'download_magic_from_id', fake_download)
        monkeypatch.setattr(ipmag, 'upload_magic', lambda **kw: (os.path.join(kw['dir_path'], 'x_upload.txt'), {}, None, None))
        top = str(tmp_path / 'project')
        magic_dir, upload_file = ipmag.validate_magic(top, contribution_id=19340, private_key='abc')
        assert magic_dir == os.path.join(top, 'MagIC') and upload_file == 'x_upload.txt'
        assert calls == {'id': 19340, 'directory': magic_dir, 'share_key': 'abc'}   # the key rides with the id
        assert os.path.exists(os.path.join(magic_dir, 'measurements.txt'))         # unpacked

    def test_a_failed_download_is_reported_not_raised(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(ipmag, 'download_magic_from_doi', lambda doi, dir_path='.': (False, 'no such DOI'))
        assert ipmag.validate_magic(str(tmp_path / 'p'), doi='10.0/nothing') == (False, False)
        assert 'no such DOI' in capsys.readouterr().out
        assert ipmag.validate_magic(str(tmp_path / 'p')) == (False, False)


class TestUploadToPrivateContribution:
    def test_the_file_is_sent_in_binary_and_the_reply_is_reported(self, tmp_path, monkeypatch):
        path = tmp_path / 'upload.txt'
        path.write_text('tab\tcontribution\n')
        seen = {}

        class Reply:
            status_code = 202

            class request:
                url = 'https://api.earthref.org/v1/MagIC/private?id=1'

        def fake_put(url, params=None, auth=None, headers=None, data=None):
            seen.update(url=url, params=params, auth=auth, mode=data.mode)
            return Reply()

        monkeypatch.setattr(ipmag.requests, 'put', fake_put)
        response = ipmag.upload_to_private_contribution(1, str(path), 'me', 'pw')
        assert response['status_code'] is True and response['errors'] == 'None'
        assert seen == {'url': 'https://api.earthref.org/v1/MagIC/private', 'params': {'id': 1},
                        'auth': ('me', 'pw'), 'mode': 'rb'}
        # a missing file is a reason, not a crash
        response = ipmag.upload_to_private_contribution(1, str(tmp_path / 'absent.txt'))
        assert response['status_code'] is False and 'absent.txt' in response['errors']

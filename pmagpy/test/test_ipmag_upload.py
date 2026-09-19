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

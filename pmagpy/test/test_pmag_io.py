"""
Tests for MagIC file I/O functions in pmag.py.

Covers magic_read (56 internal calls) and magic_write (33 calls) —
the core routines for reading and writing MagIC-formatted tab-delimited
data files used throughout PmagPy.
"""
import os

from pmagpy import pmag


# Path to a known MagIC data file in the repository
SITES_FILE = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    'data_files', 'thellier_GUI', 'Tauxe_2006_example', 'pmag_sites.txt'
)


# ---------------------------------------------------------------------------
# magic_read: read MagIC tab-delimited files
# ---------------------------------------------------------------------------

class TestMagicRead:
    """Tests for pmag.magic_read."""

    def test_returns_list_and_file_type(self):
        """magic_read returns a list of dicts and the file type string."""
        data, file_type = pmag.magic_read(SITES_FILE)
        assert isinstance(data, list)
        assert isinstance(file_type, str)
        assert file_type == 'pmag_sites'

    def test_record_count(self):
        """Known file has expected number of records (59 data rows)."""
        data, _ = pmag.magic_read(SITES_FILE)
        assert len(data) == 59

    def test_records_are_dicts_with_expected_keys(self):
        """Each record is a dictionary with MagIC column names as keys."""
        data, _ = pmag.magic_read(SITES_FILE)
        expected_keys = {'er_site_name', 'site_int', 'site_int_n',
                         'er_location_name'}
        for key in expected_keys:
            assert key in data[0], f"Missing key: {key}"

    def test_first_record_values(self):
        """Spot-check values in the first record."""
        data, _ = pmag.magic_read(SITES_FILE)
        rec = data[0]
        assert rec['er_location_name'] == '169'
        assert rec['site_int'] == '1.052e-05'

    def test_return_keys_flag(self):
        """return_keys=True adds a third return value with column names."""
        data, file_type, keys = pmag.magic_read(SITES_FILE, return_keys=True)
        assert isinstance(keys, list)
        assert 'er_site_name' in keys
        assert len(keys) > 0

    def test_missing_file_returns_empty(self):
        """Non-existent file returns empty list with 'empty_file' type."""
        data, file_type = pmag.magic_read('/nonexistent/path/file.txt')
        assert data == []
        assert file_type == 'empty_file'


# ---------------------------------------------------------------------------
# magic_write: write MagIC tab-delimited files
# ---------------------------------------------------------------------------

class TestMagicWrite:
    """Tests for pmag.magic_write."""

    def test_write_read_roundtrip(self, tmp_path):
        """Write records then read them back; data survives roundtrip."""
        recs = [
            {'specimen': 'abc01', 'dec': '10.3', 'inc': '43.0'},
            {'specimen': 'abc02', 'dec': '12.5', 'inc': '41.2'},
        ]
        outfile = str(tmp_path / 'test_output.txt')
        success, ofile = pmag.magic_write(outfile, recs, 'specimens')
        assert success is True
        assert os.path.exists(ofile)
        # Read back
        data, file_type = pmag.magic_read(ofile)
        assert file_type == 'specimens'
        assert len(data) == 2
        assert data[0]['specimen'] == 'abc01'
        assert data[1]['dec'] == '12.5'

    def test_empty_records_returns_false(self):
        """Empty record list returns (False, '')."""
        success, ofile = pmag.magic_write('/tmp/empty.txt', [], 'specimens')
        assert success is False

    def test_file_has_magic_header(self, tmp_path):
        """Written file starts with the MagIC 'tab' header line."""
        recs = [{'specimen': 'test01', 'dec': '0.0'}]
        outfile = str(tmp_path / 'header_test.txt')
        pmag.magic_write(outfile, recs, 'specimens')
        with open(outfile) as f:
            first_line = f.readline().strip()
        assert first_line.startswith('tab')
        assert 'specimens' in first_line

    def test_all_keys_present_in_output(self, tmp_path):
        """All dictionary keys appear as columns in the output file."""
        recs = [
            {'site': 'A', 'lat': '45.0', 'lon': '-120.0'},
            {'site': 'B', 'lat': '30.0', 'lon': '10.0'},
        ]
        outfile = str(tmp_path / 'keys_test.txt')
        pmag.magic_write(outfile, recs, 'sites')
        data, _ = pmag.magic_read(outfile)
        for key in ['site', 'lat', 'lon']:
            assert key in data[0], f"Missing key: {key}"

    def test_roundtrip_preserves_real_data(self, tmp_path):
        """Reading a real file, writing it, and reading again preserves data."""
        original_data, file_type = pmag.magic_read(SITES_FILE)
        outfile = str(tmp_path / 'roundtrip.txt')
        pmag.magic_write(outfile, original_data, file_type)
        recovered_data, recovered_type = pmag.magic_read(outfile)
        assert recovered_type == file_type
        assert len(recovered_data) == len(original_data)
        # Spot-check a few values from the first record
        for key in ['er_site_name', 'site_int', 'site_int_n']:
            assert recovered_data[0][key] == original_data[0][key]

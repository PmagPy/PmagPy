"""
Tests for data handling and parsing functions in pmag.py.

Covers fillkeys (dictionary key reconciliation), parse_site (site name
extraction from sample names), and get_specs (unique specimen name
extraction) — infrastructure functions used throughout PmagPy for
MagIC data manipulation.
"""
from pmagpy import pmag


# ---------------------------------------------------------------------------
# fillkeys: reconcile dictionary keys across records
# ---------------------------------------------------------------------------

class TestFillkeys:
    """Tests for pmag.fillkeys."""

    def test_uniform_records_unchanged(self):
        """Records with identical keys pass through unchanged."""
        recs = [
            {'site': 'A', 'lat': '45'},
            {'site': 'B', 'lat': '30'},
        ]
        out, keys = pmag.fillkeys(recs)
        assert len(out) == 2
        assert set(keys) == {'site', 'lat'}

    def test_missing_keys_filled_with_empty_string(self):
        """Records missing keys get them filled with empty strings."""
        recs = [
            {'site': 'A', 'lat': '45'},
            {'site': 'B', 'lon': '10'},
        ]
        out, keys = pmag.fillkeys(recs)
        assert out[0]['lon'] == ''
        assert out[1]['lat'] == ''

    def test_all_keys_returned(self):
        """Returned keylist contains all keys from all records."""
        recs = [
            {'a': '1'},
            {'b': '2'},
            {'c': '3'},
        ]
        _, keys = pmag.fillkeys(recs)
        assert set(keys) == {'a', 'b', 'c'}

    def test_existing_values_preserved(self):
        """Existing values are not overwritten."""
        recs = [
            {'site': 'A', 'lat': '45'},
            {'site': 'B'},
        ]
        out, _ = pmag.fillkeys(recs)
        assert out[0]['site'] == 'A'
        assert out[0]['lat'] == '45'
        assert out[1]['site'] == 'B'

    def test_single_record(self):
        """Single record returns unchanged with its keys."""
        recs = [{'specimen': 'abc01', 'dec': '10'}]
        out, keys = pmag.fillkeys(recs)
        assert len(out) == 1
        assert set(keys) == {'specimen', 'dec'}

    def test_empty_list(self):
        """Empty record list returns empty results."""
        out, keys = pmag.fillkeys([])
        assert out == []
        assert keys == []

    def test_record_count_preserved(self):
        """Number of records is preserved."""
        recs = [{'a': '1'}, {'b': '2'}, {'c': '3'}, {'d': '4'}]
        out, _ = pmag.fillkeys(recs)
        assert len(out) == 4


# ---------------------------------------------------------------------------
# parse_site: extract site name from sample name
# ---------------------------------------------------------------------------

class TestParseSite:
    """Tests for pmag.parse_site."""

    def test_convention_1_peel_last_char(self):
        """Convention 1: site = sample minus last character (SIO style)."""
        assert pmag.parse_site('TG001a', '1', 1) == 'TG001'
        assert pmag.parse_site('ABC123x', '1', 1) == 'ABC123'

    def test_convention_2_split_by_dash(self):
        """Convention 2: site = part before first dash (PGL style)."""
        assert pmag.parse_site('BG94-1', '2', 1) == 'BG94'
        assert pmag.parse_site('SITE01-A2', '2', 1) == 'SITE01'

    def test_convention_3_split_by_dot(self):
        """Convention 3: site = part before first dot."""
        assert pmag.parse_site('SITE01.A2', '3', 1) == 'SITE01'
        assert pmag.parse_site('ABC.123', '3', 1) == 'ABC'

    def test_convention_4_peel_z_chars(self):
        """Convention 4: site = sample[0:-(Z-1)] (Z is sample designation length)."""
        # Z=3 means sample designation is 3 chars, so k=Z-1=2 chars peeled
        assert pmag.parse_site('SITE001', '4', 3) == 'SITE0'
        assert pmag.parse_site('ABC12345', '4', 5) == 'ABC1'

    def test_convention_5_sample_equals_site(self):
        """Convention 5: site = sample (identical)."""
        assert pmag.parse_site('MySample', '5', 1) == 'MySample'

    def test_convention_7_take_first_z_chars(self):
        """Convention 7: site = first Z characters of sample."""
        assert pmag.parse_site('ABCXYZ', '7', 3) == 'ABC'
        assert pmag.parse_site('SITE001A', '7', 7) == 'SITE001'

    def test_convention_8_split_by_underscore(self):
        """Convention 8: returns (specimen, sample, site) tuple split by underscore."""
        result = pmag.parse_site('SITE_SAMP_SPEC', '8', 1)
        assert isinstance(result, tuple)
        assert result[2] == 'SITE'  # site is first part
        assert result[1] == 'SITE_SAMP'  # sample is first two parts

    def test_integer_convention_accepted(self):
        """Integer convention values are accepted (converted internally)."""
        assert pmag.parse_site('TG001a', 1, 1) == 'TG001'


# ---------------------------------------------------------------------------
# get_specs: extract unique specimen names
# ---------------------------------------------------------------------------

class TestGetSpecs:
    """Tests for pmag.get_specs."""

    def test_magic3_format(self):
        """Extracts specimen names from MagIC 3.0 'specimen' key."""
        data = [
            {'specimen': 'abc01'},
            {'specimen': 'abc02'},
            {'specimen': 'abc01'},  # duplicate
        ]
        specs = pmag.get_specs(data)
        assert specs == ['abc01', 'abc02']

    def test_magic2_format(self):
        """Extracts specimen names from MagIC 2.x 'er_specimen_name' key."""
        data = [
            {'er_specimen_name': 'spec_a'},
            {'er_specimen_name': 'spec_b'},
        ]
        specs = pmag.get_specs(data)
        assert specs == ['spec_a', 'spec_b']

    def test_sorted_output(self):
        """Output is sorted alphabetically."""
        data = [
            {'specimen': 'ccc'},
            {'specimen': 'aaa'},
            {'specimen': 'bbb'},
        ]
        specs = pmag.get_specs(data)
        assert specs == ['aaa', 'bbb', 'ccc']

    def test_deduplication(self):
        """Duplicate specimen names are removed."""
        data = [{'specimen': 'abc01'}] * 5
        specs = pmag.get_specs(data)
        assert specs == ['abc01']

    def test_single_specimen(self):
        """Single specimen returns a one-element list."""
        data = [{'specimen': 'only_one'}]
        specs = pmag.get_specs(data)
        assert specs == ['only_one']

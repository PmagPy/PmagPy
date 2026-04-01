"""
Tests for data structure utility functions in pmag.py.

Covers get_dictitem (107 internal calls), get_dictkey (17 calls),
get_list (27 calls), sort_diclist, and adjust_to_360 — the core
data-wrangling helpers used throughout PmagPy for filtering, extracting,
and normalizing MagIC-format records.
"""
from pmagpy import pmag


# ---------------------------------------------------------------------------
# Sample data used across multiple test classes
# ---------------------------------------------------------------------------

SAMPLE_RECS = [
    {'specimen': 'abc01a', 'dec': '10.3', 'inc': '43', 'int': '5.2e-6'},
    {'specimen': 'abc01b', 'dec': '12.3', 'inc': '42', 'int': '4.9e-6'},
    {'specimen': 'abc02a', 'dec': '350.1', 'inc': '55', 'int': '6.1e-6'},
    {'specimen': 'xyz01a', 'dec': '180.0', 'inc': '-30', 'int': '3.0e-6'},
]


# ---------------------------------------------------------------------------
# get_dictitem: filter list-of-dicts by key-value conditions
# ---------------------------------------------------------------------------

class TestGetDictitem:
    """Tests for pmag.get_dictitem (107 internal call sites)."""

    def test_docstring_example(self):
        """Verify the docstring example."""
        In = [{'specimen': 'abc01b01', 'dec': '10.3', 'inc': '43', 'int': '5.2e-6'},
              {'specimen': 'abc01b02', 'dec': '12.3', 'inc': '42', 'int': '4.9e-6'}]
        result = pmag.get_dictitem(In, 'specimen', 'abc01b02', 'T')
        assert len(result) == 1
        assert result[0]['specimen'] == 'abc01b02'

    def test_flag_T_exact_match(self):
        """flag='T' returns records where key equals value (case-insensitive)."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'specimen', 'abc01a', 'T')
        assert len(result) == 1
        assert result[0]['specimen'] == 'abc01a'

    def test_flag_T_case_insensitive(self):
        """flag='T' matching is case-insensitive."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'specimen', 'ABC01A', 'T')
        assert len(result) == 1

    def test_flag_F_not_equal(self):
        """flag='F' returns records where key does not equal value."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'specimen', 'abc01a', 'F')
        assert len(result) == 3
        for rec in result:
            assert rec['specimen'] != 'abc01a'

    def test_flag_has_substring(self):
        """flag='has' returns records where value is a substring of key's value."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'specimen', 'abc', 'has')
        assert len(result) == 3  # abc01a, abc01b, abc02a

    def test_flag_not_substring(self):
        """flag='not' returns records where value is NOT a substring."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'specimen', 'abc', 'not')
        assert len(result) == 1
        assert result[0]['specimen'] == 'xyz01a'

    def test_flag_min_threshold(self):
        """flag='min' returns records where float(key) >= float(value)."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'inc', '43', 'min')
        assert len(result) == 2  # inc='43' and inc='55'

    def test_flag_max_threshold(self):
        """flag='max' returns records where float(key) <= float(value)."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'inc', '42', 'max')
        assert len(result) == 2  # inc='42' and inc='-30'

    def test_flag_eval_exact_numeric(self):
        """flag='eval' returns records where float(key) == float(value)."""
        result = pmag.get_dictitem(SAMPLE_RECS, 'inc', '43', 'eval')
        assert len(result) == 1
        assert result[0]['specimen'] == 'abc01a'

    def test_empty_input_returns_empty(self):
        """Empty input list returns empty list for all flags."""
        assert pmag.get_dictitem([], 'k', 'v', 'T') == []

    def test_missing_key_skips_record(self):
        """Records missing the key are silently skipped."""
        recs = [{'a': '1'}, {'b': '2'}]
        result = pmag.get_dictitem(recs, 'a', '1', 'T')
        assert len(result) == 1

    def test_flag_min_skips_blanks(self):
        """flag='min' skips records with blank values for the key."""
        recs = [{'val': '10'}, {'val': ''}, {'val': '20'}]
        result = pmag.get_dictitem(recs, 'val', '5', 'min')
        assert len(result) == 2  # blank is skipped, 10 and 20 pass


# ---------------------------------------------------------------------------
# get_dictkey: extract a single key from list-of-dicts
# ---------------------------------------------------------------------------

class TestGetDictkey:
    """Tests for pmag.get_dictkey."""

    def test_docstring_example(self):
        """Verify the docstring example."""
        In = [{'specimen': 'abc01b01', 'dec': '10.3', 'inc': '43', 'int': '5.2e-6'},
              {'specimen': 'abc01b02', 'dec': '12.3', 'inc': '42', 'int': '4.9e-6'}]
        result = pmag.get_dictkey(In, 'specimen', '')
        assert result == ['abc01b01', 'abc01b02']

    def test_string_dtype(self):
        """dtype='' returns raw string values."""
        result = pmag.get_dictkey(SAMPLE_RECS, 'dec', '')
        assert result == ['10.3', '12.3', '350.1', '180.0']

    def test_float_dtype(self):
        """dtype='f' returns float values."""
        result = pmag.get_dictkey(SAMPLE_RECS, 'dec', 'f')
        assert all(isinstance(v, float) for v in result)
        assert result[0] == 10.3

    def test_int_dtype(self):
        """dtype='int' returns integer values."""
        result = pmag.get_dictkey(SAMPLE_RECS, 'inc', 'int')
        assert all(isinstance(v, int) for v in result)
        assert result[0] == 43

    def test_float_dtype_blank_returns_zero(self):
        """dtype='f' converts blank strings to 0."""
        recs = [{'val': ''}, {'val': '3.14'}]
        result = pmag.get_dictkey(recs, 'val', 'f')
        assert result == [0, 3.14]

    def test_preserves_order(self):
        """Output order matches input order."""
        result = pmag.get_dictkey(SAMPLE_RECS, 'specimen', '')
        assert result == ['abc01a', 'abc01b', 'abc02a', 'xyz01a']


# ---------------------------------------------------------------------------
# get_list: extract unique colon-delimited values from a key
# ---------------------------------------------------------------------------

class TestGetList:
    """Tests for pmag.get_list."""

    def test_single_values(self):
        """Records with single values are collected and deduplicated."""
        data = [{'method': 'LP-DIR'}, {'method': 'LP-PI'}, {'method': 'LP-DIR'}]
        result = pmag.get_list(data, 'method')
        parts = result.split(':')
        assert 'LP-DIR' in parts
        assert 'LP-PI' in parts
        assert len(parts) == 2  # deduplicated

    def test_colon_delimited_values(self):
        """Colon-delimited values within records are split and deduplicated."""
        data = [{'method': 'LP-DIR:LP-PI'}, {'method': 'LP-PI:LP-AN'}]
        result = pmag.get_list(data, 'method')
        parts = result.split(':')
        assert 'LP-DIR' in parts
        assert 'LP-PI' in parts
        assert 'LP-AN' in parts
        assert len(parts) == 3

    def test_empty_values_return_empty_string(self):
        """Records with empty string values return empty string."""
        data = [{'method': ''}]
        result = pmag.get_list(data, 'method')
        assert result == ''


# ---------------------------------------------------------------------------
# sort_diclist: sort list-of-dicts by a key
# ---------------------------------------------------------------------------

class TestSortDiclist:
    """Tests for pmag.sort_diclist."""

    def test_docstring_example(self):
        """Verify the docstring example."""
        lst = [{'key1': 10, 'key2': 2}, {'key1': 1, 'key2': 20}]
        result = pmag.sort_diclist(lst, 'key1')
        assert result[0]['key1'] == 1
        assert result[1]['key1'] == 10

    def test_numeric_sort(self):
        """Sorts numerically by numeric key values."""
        lst = [{'n': 30}, {'n': 10}, {'n': 20}]
        result = pmag.sort_diclist(lst, 'n')
        assert [d['n'] for d in result] == [10, 20, 30]

    def test_string_sort_by_length(self):
        """String values are sorted by length."""
        lst = [{'name': 'abc'}, {'name': 'a'}, {'name': 'ab'}]
        result = pmag.sort_diclist(lst, 'name')
        assert [d['name'] for d in result] == ['a', 'ab', 'abc']

    def test_preserves_all_keys(self):
        """All keys in each dictionary are preserved after sorting."""
        lst = [{'a': 2, 'b': 'x'}, {'a': 1, 'b': 'y'}]
        result = pmag.sort_diclist(lst, 'a')
        assert result[0] == {'a': 1, 'b': 'y'}
        assert result[1] == {'a': 2, 'b': 'x'}


# ---------------------------------------------------------------------------
# adjust_to_360: normalize angular values to 0–360
# ---------------------------------------------------------------------------

class TestAdjustTo360:
    """Tests for pmag.adjust_to_360."""

    def test_negative_declination_wrapped(self):
        """Negative declination is wrapped to 0–360."""
        result = pmag.adjust_to_360(-10, 'dir_dec')
        assert result == 350.0

    def test_over_360_wrapped(self):
        """Value > 360 is wrapped via modulo."""
        result = pmag.adjust_to_360(370, 'dir_dec')
        assert result == 10.0

    def test_in_range_unchanged(self):
        """Value already in 0–360 is returned unchanged."""
        result = pmag.adjust_to_360(180.0, 'dir_dec')
        assert result == 180.0

    def test_non_angle_key_unchanged(self):
        """Non-angle keys are not adjusted regardless of value."""
        result = pmag.adjust_to_360(-10, 'dir_inc')
        assert result == -10

    def test_longitude_key_adjusted(self):
        """Keys containing '_lon' are adjusted."""
        result = pmag.adjust_to_360(-30, 'vgp_lon')
        assert result == 330.0

    def test_azimuth_key_adjusted(self):
        """Keys containing '_azimuth' are adjusted."""
        result = pmag.adjust_to_360(400, 'sample_azimuth')
        assert result == 40.0

    def test_empty_value_returns_empty_string(self):
        """Falsy values return empty string."""
        result = pmag.adjust_to_360('', 'dir_dec')
        assert result == ''

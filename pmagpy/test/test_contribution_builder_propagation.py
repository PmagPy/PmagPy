"""
Tests for Contribution.propagate_name_down and the propagate_location_to_*
convenience methods.

propagate_name_down looks a name up through as many levels as needed:
specimens for the sample of a measurement, samples for its site, sites for
its location. The guards added around the two lower merges in 2017 tested
the wrong column, so those merges could never run and a call that needed
more than one level did nothing, without a message. A call for 'sample' or
'specimen', for which there is no lower level, asked for a table named ""
and printed '-W- "" is not a valid MagIC table type' (PmagPy/PmagPy#576).

data_files/convert_2_magic/jr6_magic is used because each of its tables
holds only its own name and that of its parent: measurements have a
specimen, specimens a sample, samples a site and sites a location.
"""
import os
import shutil

import pandas as pd
import pytest

from pmagpy import contribution_builder as cb

DATA_FILES = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'data_files')
JR6 = os.path.join(DATA_FILES, 'convert_2_magic', 'jr6_magic')
TABLES = ['measurements', 'specimens', 'samples', 'sites', 'locations']
BAD_TABLE_WARNING = 'is not a valid MagIC table type'


def read_table(name):
    return pd.read_csv(os.path.join(JR6, name + '.txt'), sep='\t', header=1, dtype=str)


@pytest.fixture(scope="module")
def expected():
    """Names of each level for every measurement, from plain pandas merges."""
    specimens = read_table('specimens')[['specimen', 'sample']].drop_duplicates('specimen')
    samples = read_table('samples')[['sample', 'site']].drop_duplicates('sample')
    sites = read_table('sites')[['site', 'location']].drop_duplicates('site')
    names = read_table('measurements')[['measurement', 'specimen']]
    names = names.merge(specimens, on='specimen', how='left')
    names = names.merge(samples, on='sample', how='left')
    names = names.merge(sites, on='site', how='left')
    assert names.notnull().all().all()
    return names


@pytest.fixture
def working_dir(tmp_path):
    # work on a copy: reading a measurements table can write it back
    for table in TABLES:
        shutil.copy(os.path.join(JR6, table + '.txt'), tmp_path)
    return str(tmp_path)


@pytest.fixture
def contribution(working_dir):
    return cb.Contribution(working_dir, read_tables=TABLES)


def names_in(contribution, table, columns):
    df = contribution.tables[table].df
    return df[list(columns)].astype(str).reset_index(drop=True)


class TestPropagateNameDown:

    def test_location_reaches_measurements_in_one_call(self, contribution, expected):
        returned = contribution.propagate_name_down('location', 'measurements')
        columns = ['specimen', 'sample', 'site', 'location']
        found = names_in(contribution, 'measurements', columns)
        pd.testing.assert_frame_equal(found, expected[columns], check_dtype=False)
        assert returned is contribution.tables['measurements'].df

    @pytest.mark.parametrize("col_name, table, key", [
        ('sample', 'measurements', 'specimen'),
        ('site', 'measurements', 'specimen'),
        ('site', 'specimens', 'specimen'),
        ('location', 'specimens', 'specimen'),
        ('location', 'samples', 'sample'),
        ('location', 'sites', 'site'),
    ])
    def test_single_call_fills_the_column(self, contribution, expected, col_name, table, key):
        contribution.propagate_name_down(col_name, table)
        found = names_in(contribution, table, [key, col_name]).drop_duplicates()
        lookup = expected[[key, col_name]].drop_duplicates()
        merged = found.merge(lookup, on=key, how='left', suffixes=('', '_expected'))
        assert len(merged) == len(found)
        assert (merged[col_name] == merged[col_name + '_expected']).all()

    def test_one_call_matches_the_call_per_level_wrapper(self, working_dir):
        one_call = cb.Contribution(working_dir, read_tables=TABLES)
        one_call.propagate_name_down('location', 'measurements')
        per_level = cb.Contribution(working_dir, read_tables=TABLES)
        per_level.propagate_location_to_measurements()
        columns = ['specimen', 'sample', 'site', 'location']
        pd.testing.assert_frame_equal(names_in(one_call, 'measurements', columns),
                                      names_in(per_level, 'measurements', columns))

    def test_complete_column_is_left_alone(self, contribution):
        before = contribution.tables['specimens'].df.copy()
        contribution.propagate_name_down('sample', 'specimens')
        pd.testing.assert_frame_equal(contribution.tables['specimens'].df, before)


class TestLevelsThatDoNotExist:
    # 'sample' has no level below the measurements, and 'specimen' has
    # nothing below it at all

    @pytest.mark.parametrize("col_name, table", [
        ('sample', 'measurements'),
        ('specimen', 'measurements'),
    ])
    def test_no_request_for_a_nameless_table(self, contribution, capsys, col_name, table):
        contribution.propagate_name_down(col_name, table, verbose=True)
        assert BAD_TABLE_WARNING not in capsys.readouterr().out

    def test_blank_sample_name_in_specimens(self, contribution, capsys):
        specimens = contribution.tables['specimens'].df
        specimens.iloc[0, specimens.columns.get_loc('sample')] = None
        contribution.propagate_name_down('sample', 'specimens', verbose=True)
        assert BAD_TABLE_WARNING not in capsys.readouterr().out

    def test_measurements_without_a_measurement_column(self, contribution, expected, capsys):
        # this used to print the warning and give up on every level
        table = contribution.tables['measurements']
        table.df = table.df.drop(columns=['measurement'])
        contribution.propagate_location_to_measurements()
        assert BAD_TABLE_WARNING not in capsys.readouterr().out
        columns = ['specimen', 'sample', 'site', 'location']
        pd.testing.assert_frame_equal(names_in(contribution, 'measurements', columns),
                                      expected[columns], check_dtype=False)


class TestMissingTables:

    def test_propagation_stops_at_a_table_that_cannot_be_read(self, working_dir, capsys):
        os.remove(os.path.join(working_dir, 'samples.txt'))
        contribution = cb.Contribution(working_dir, read_tables=['measurements', 'specimens', 'sites'])
        contribution.propagate_name_down('location', 'measurements', verbose=True)
        measurements = contribution.tables['measurements'].df
        assert measurements['sample'].notnull().all()
        assert 'site' not in measurements.columns
        assert 'location' not in measurements.columns
        assert "Couldn't read in samples data" in capsys.readouterr().out

    def test_table_to_fill_cannot_be_read(self, tmp_path):
        contribution = cb.Contribution(str(tmp_path), read_tables=[])
        assert contribution.propagate_name_down('location', 'measurements') is None

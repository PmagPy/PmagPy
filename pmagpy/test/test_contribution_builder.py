"""
Tests for pmagpy.contribution_builder: the MagicDataFrame that holds one MagIC
table and the Contribution that links the tables of a study.

Most tests build small tables by hand, written to a temporary directory and read
back, so that blank cells arrive the way they do from a real MagIC file and the
expected result can be worked out by eye. data_files is used only where the
real files matter. Name propagation down the hierarchy is covered in
test_contribution_builder_propagation.py.

Several methods fill missing values with np.where(target, target, new), which
treats NaN as present. Blank cells read from a file are NaN in numeric columns
(and, under pandas 3, in text columns as well), so those blanks are never
filled. The tests for that behavior are marked xfail until it is fixed.
"""
import os

import numpy as np
import pandas as pd
import pytest

from pmagpy import contribution_builder as cb

PANDAS_3 = int(pd.__version__.split('.')[0]) >= 3

NAN_IS_PRESENT = ("np.where(target, target, new) treats NaN as a value (propagate_cols, "
                  "propagate_cols_up and propagate_ages), so a blank that is NaN is never "
                  "filled; propagate_average_up and propagate_min_max_up use a not_null mask")


@pytest.fixture(autouse=True)
def work_in_tmp_path(tmp_path, monkeypatch):
    """Run every test in tmp_path: some methods write tables to the working directory."""
    monkeypatch.chdir(tmp_path)


def write_table(directory, dtype, records, fname=None):
    """
    Write records as a MagIC 3 tab-delimited table.

    Args:
        directory (str or Path): directory to write into
        dtype (str): MagIC table name, e.g. 'sites'
        records (list of dict): one dict per row; '' leaves a blank cell
        fname (str, optional): file name, default '<dtype>.txt'

    Returns:
        str: path of the written file
    """
    path = os.path.join(str(directory), fname or dtype + '.txt')
    with open(path, 'w') as f:
        f.write('tab\t{}\n'.format(dtype))
        pd.DataFrame(records).to_csv(f, sep='\t', index=False)
    return path


# ----------------------------------------------------------------------------
# MagicDataFrame


@pytest.fixture
def sites(tmp_path):
    """
    A sites table read from file: s1 has a geographic and a tilt-corrected
    row, s2 a row without a tilt correction, s3 a row without a direction.
    """
    fname = write_table(tmp_path, 'sites', [
        {'site': 's1', 'location': 'L', 'dir_dec': 10., 'dir_inc': 20.,
         'dir_tilt_correction': 0, 'lat': 5.0, 'method_codes': 'LP-DIR-AF:DE-BFL'},
        {'site': 's1', 'location': 'L', 'dir_dec': 15., 'dir_inc': 25.,
         'dir_tilt_correction': 100, 'lat': '', 'method_codes': 'LP-DIR-AF:DE-BFL'},
        {'site': 's2', 'location': 'L', 'dir_dec': 30., 'dir_inc': 40.,
         'dir_tilt_correction': '', 'lat': '', 'method_codes': 'LP-DIR-T:DE-BFP'},
        {'site': 's3', 'location': 'L', 'dir_dec': '', 'dir_inc': '',
         'dir_tilt_correction': 100, 'lat': 7.0, 'method_codes': 'LP-DIR-T'},
    ])
    return cb.MagicDataFrame(fname)


class TestMagicDataFrameInit:

    @pytest.mark.parametrize('how', ['constructor', 'add_data'])
    def test_from_data_list(self, how):
        """A list of dicts becomes a table indexed by the item name."""
        data = [{'specimen': 'spec1', 'sample': 'samp1'},
                {'specimen': 'spec2', 'sample': 'samp2'}]
        if how == 'constructor':
            magic_df = cb.MagicDataFrame(dtype='specimens', data=data)
        else:
            magic_df = cb.MagicDataFrame(dtype='specimens')
            magic_df.add_data(data)
        assert magic_df.dtype == 'specimens'
        assert magic_df.df.index.name == 'specimen name'
        assert sorted(magic_df.df.index) == ['spec1', 'spec2']
        assert magic_df.df.loc['spec2', 'sample'] == 'samp2'

    def test_empty_table_of_a_dtype(self):
        magic_df = cb.MagicDataFrame(dtype='samples', columns=['site', 'lat'])
        assert magic_df.dtype == 'samples'
        assert len(magic_df.df) == 0
        assert {'sample', 'site', 'lat'} <= set(magic_df.df.columns)

    def test_column_groups_from_the_data_model(self):
        """groups= adds every column of that data model group."""
        magic_df = cb.MagicDataFrame(dtype='sites', groups=['Age'])
        assert {'age', 'age_low', 'age_high', 'age_unit'} <= set(magic_df.df.columns)

    def test_from_file(self, sites):
        """The dtype comes from the header line and the index holds the names as strings."""
        assert sites.dtype == 'sites'
        assert list(sites.df.index) == ['s1', 's1', 's2', 's3']
        assert list(sites.df['site']) == list(sites.df.index)
        assert pd.isnull(sites.df.loc['s2', 'lat'])

    def test_integer_names_become_strings(self, tmp_path):
        fname = write_table(tmp_path, 'sites', [{'site': 1, 'lat': 10.}, {'site': 2, 'lat': 11.}])
        assert list(cb.MagicDataFrame(fname).df.index) == ['1', '2']

    def test_empty_file(self, tmp_path):
        fname = tmp_path / 'sites.txt'
        fname.write_text('')
        assert cb.MagicDataFrame(str(fname)).dtype == 'empty'

    def test_measurement_names_and_sequence_are_added(self, tmp_path):
        """
        A measurements table without measurement and sequence columns gets
        them, built from experiment + treat_step_num. (Reading such a table
        also rewrites the file with them, which is not asserted here.)
        """
        fname = write_table(tmp_path, 'measurements', [
            {'experiment': 'a1-LP-DIR-AF', 'specimen': 'a1', 'treat_step_num': 1, 'magn_moment': 1e-5},
            {'experiment': 'a1-LP-DIR-AF', 'specimen': 'a1', 'treat_step_num': 2, 'magn_moment': 5e-6}])
        meas = cb.MagicDataFrame(fname)
        assert list(meas.df['measurement']) == ['a1-LP-DIR-AF1', 'a1-LP-DIR-AF2']
        assert list(meas.df['sequence']) == [1, 2]


class TestMagicDataFrameEdit:

    def test_add_row(self, sites):
        """A new key adds a column; a repeated name adds a row rather than replacing one."""
        sites.add_row('s4', {'site': 's4', 'new_col': 'new_val'})
        assert sites.df.iloc[-1]['new_col'] == 'new_val'
        sites.add_row('s4', {'site': 's4', 'lat': 9.0})
        assert len(sites.df.loc['s4']) == 2
        assert len(sites.df) == 6

    def test_add_blank_row(self, sites):
        sites.add_blank_row('blank')
        assert 'blank' in sites.df.index
        assert sites.df.loc['blank'].isnull().all()

    @pytest.mark.xfail(strict=True, reason="update_row assigns the values of row_data "
                       "in key order, not by column name: misplaced under pandas 2, "
                       "a TypeError under pandas 3")
    def test_update_row_by_column_name(self):
        magic_df = cb.MagicDataFrame(dtype='sites', data=[
            {'site': 'a', 'lat': 1.0, 'lithologies': 'Basalt'},
            {'site': 'b', 'lat': 2.0, 'lithologies': 'Gabbro'}])
        magic_df.update_row(1, {'lithologies': 'Diabase', 'site': 'b', 'lat': 2.5,
                                'new_col': 'new_val'})
        row = magic_df.df.iloc[1]
        assert (row['site'], row['lat'], row['lithologies'], row['new_col']) == \
            ('b', 2.5, 'Diabase', 'new_val')

    def test_delete_row_by_position(self, sites):
        sites.delete_row(2)
        assert list(sites.df.index) == ['s1', 's1', 's3']

    def test_delete_rows_by_condition(self, sites):
        sites.delete_rows(sites.df['dir_dec'].isnull())
        assert list(sites.df.index) == ['s1', 's1', 's2']

    def test_update_record(self, sites):
        """
        The first record that matches the name and condition is updated and
        the other matching records are removed; with no match a record is
        added unless update_only is set.
        """
        is_af = sites.df['method_codes'].str.contains('LP-DIR-AF').fillna(False)
        sites.update_record('s1', {'lat': 6.0}, is_af)
        assert len(sites.df.loc[['s1']]) == 1
        assert sites.df.loc['s1', 'lat'] == 6.0
        assert sites.df.loc['s1', 'dir_dec'] == 10.
        is_af = sites.df['method_codes'].str.contains('LP-DIR-AF').fillna(False)
        sites.update_record('s2', {'lat': 1.0}, is_af, update_only=True)
        assert len(sites.df.loc[['s2']]) == 1
        assert pd.isnull(sites.df.loc['s2', 'lat'])
        sites.update_record('s2', {'site': 's2', 'lat': 1.0}, is_af)
        assert len(sites.df.loc[['s2']]) == 2

    def test_drop_stub_rows(self, sites):
        """Rows holding nothing but names are dropped."""
        sites.add_row('s1', {'site': 's1', 'location': 'L'})
        sites.drop_stub_rows(['site', 'location'])
        assert len(sites.df.loc[['s1']]) == 2

    def test_front_and_backfill(self, sites):
        """Values are filled among the rows of one item only."""
        unchanged = sites.front_and_backfill(['lat'], inplace=False)
        assert pd.isnull(sites.df.iloc[1]['lat'])
        assert list(unchanged['lat'].fillna(-1)) == [5.0, 5.0, -1, 7.0]
        sites.front_and_backfill(['lat'])
        assert list(sites.df['lat'].fillna(-1)) == [5.0, 5.0, -1, 7.0]

    def test_sort_dataframe_cols(self, sites):
        """The name column comes first, then the columns by data model group."""
        sites.df = sites.df[['method_codes', 'dir_inc', 'site', 'lat', 'location', 'dir_dec',
                             'dir_tilt_correction']]
        sites.sort_dataframe_cols()
        assert list(sites.df.columns) == ['site', 'location', 'dir_dec', 'dir_inc',
                                          'dir_tilt_correction', 'lat', 'method_codes']

    def test_all_to_str(self):
        """Numbers become strings without a trailing .0 or floating point noise."""
        magic_df = cb.MagicDataFrame(dtype='sites', data=[
            {'site': 'x', 'age': 0.1 + 0.2, 'n': 3.0, 'k': 2,
             'kept': '2.50', 'trimmed': '4.0', 'noise': '0.1000000000001'}])
        magic_df.all_to_str()
        assert magic_df.df.iloc[0].to_dict() == {
            'site': 'x', 'age': '0.3', 'n': '3', 'k': '2',
            'kept': '2.50', 'trimmed': '4', 'noise': '0.1'}

    def test_write_and_read_back(self, sites, tmp_path):
        """A written table reads back the same, without the temporary num column."""
        sites.df['num'] = range(len(sites.df))
        outfile = sites.write_magic_file(custom_name='out_sites.txt', dir_path=str(tmp_path))
        with open(outfile) as f:
            assert f.readline().split('\t')[:2] == ['tab', 'sites\n']
        reread = cb.MagicDataFrame(outfile)
        assert 'num' not in reread.df.columns
        cols = ['site', 'dir_dec', 'dir_inc', 'lat', 'method_codes']
        pd.testing.assert_frame_equal(reread.df[cols], sites.df[cols], check_dtype=False)


class TestMagicDataFrameQueries:

    def test_convert_to_pmag_data_list(self, sites):
        """Every value is a string, with '' for blanks, as pmag.magic_read gives."""
        records = sites.convert_to_pmag_data_list('lst')
        assert len(records) == 4
        assert records[2]['site'] == 's2'
        assert records[2]['lat'] == ''
        assert records[2]['dir_dec'] == '30.0'
        by_name = sites.convert_to_pmag_data_list('dict')
        assert set(by_name) == {'s1', 's2', 's3'}
        assert by_name['s3']['dir_dec'] == ''

    def test_get_name(self, sites):
        """The first non-null value in the table, a slice, or the rows for some names."""
        assert sites.get_name('method_codes') == 'LP-DIR-AF:DE-BFL'
        assert sites.get_name('method_codes', index_names=['s2']) == 'LP-DIR-T:DE-BFP'
        assert sites.get_name('method_codes', df_slice=sites.df.iloc[3:]) == 'LP-DIR-T'
        assert sites.get_name('not_a_column') == ''

    def test_get_first_non_null_value(self, sites):
        assert sites.get_first_non_null_value('s1', 'lat') == 5.0
        assert sites.get_first_non_null_value('s1', 'dir_tilt_correction') == 0

    def test_get_di_block(self, sites):
        """Directions in the requested coordinates, without codes in excl or blank directions."""
        assert sites.get_di_block(df_slice='all') == [[15., 25.]]
        assert sites.get_di_block(df_slice='all', ignore_tilt=True) == \
            [[10., 20.], [15., 25.], [30., 40.]]
        assert sites.get_di_block(df_slice='all', ignore_tilt=True, excl=['DE-BFP']) == \
            [[10., 20.], [15., 25.]]
        assert sites.get_di_block(do_index=True, item_names=['s1'], tilt_corr='0') == [[10., 20.]]

    @pytest.mark.xfail(strict=True, reason="the test for a blank tilt correction is "
                       "`column == None`, which is never true")
    def test_get_di_block_geographic_includes_blank_tilt_correction(self, sites):
        assert sites.get_di_block(df_slice='all', tilt_corr='0') == [[10., 20.], [30., 40.]]

    def test_get_records_for_code(self, sites):
        """Exact code match by default, partial match on request, or records without the code."""
        assert list(sites.get_records_for_code('LP-DIR').index) == []
        assert list(sites.get_records_for_code('LP-DIR-T').index) == ['s2', 's3']
        assert list(sites.get_records_for_code('LP-DIR', strict_match=False).index) == \
            ['s1', 's1', 's2', 's3']
        assert list(sites.get_records_for_code('DE-BFL', incl=False).index) == ['s2', 's3']
        assert list(sites.get_records_for_code('LP-DIR-T', use_slice=True,
                                               sli=sites.df.iloc[:3]).index) == ['s2']


# ----------------------------------------------------------------------------
# Contribution


@pytest.fixture
def study(tmp_path):
    """
    A small study written to file: two locations, three sites, samples with
    lat/lon and lithologies, specimens, and an ages table.

    s1 has two samples (lat 10 and 20, lon 20 and 40) and a blank lat/lon;
    s2 has its own lat/lon; s3 has a blank age that the ages table supplies.
    """
    d = tmp_path / 'study'
    d.mkdir()
    write_table(d, 'locations', [{'location': 'L1'}, {'location': 'L2', 'age_high': 999}])
    write_table(d, 'sites', [
        {'site': 's1', 'location': 'L1', 'lat': '', 'lon': '', 'age': 100, 'age_unit': 'Ma',
         'lithologies': '', 'geologic_types': 'Lava Flow', 'geologic_classes': 'Extrusive'},
        {'site': 's2', 'location': 'L1', 'lat': 45.0, 'lon': 10.0, 'age': 300, 'age_unit': 'Ma',
         'lithologies': 'Gabbro', 'geologic_types': 'Intrusion', 'geologic_classes': 'Intrusive'},
        {'site': 's3', 'location': 'L2', 'lat': 50.0, 'lon': 15.0, 'age': '', 'age_unit': '',
         'lithologies': 'Basalt', 'geologic_types': 'Lava Flow', 'geologic_classes': 'Extrusive'}])
    write_table(d, 'samples', [
        {'sample': 'a', 'site': 's1', 'lat': 10.0, 'lon': 20.0, 'lithologies': 'basalt'},
        {'sample': 'b', 'site': 's1', 'lat': 20.0, 'lon': 40.0, 'lithologies': 'diabase:basalt'},
        {'sample': 'c', 'site': 's2', 'lat': 0.0, 'lon': 0.0, 'lithologies': ''},
        {'sample': 'd', 'site': 's3', 'lat': 50.0, 'lon': 15.0, 'lithologies': 'Basalt'}])
    write_table(d, 'specimens', [{'specimen': 'a1', 'sample': 'a'}, {'specimen': 'c1', 'sample': 'c'}])
    write_table(d, 'ages', [
        {'site': 's3', 'location': 'L2', 'age': 50, 'age_unit': 'Ma'},
        {'site': 's1', 'location': 'L1', 'age': 111, 'age_unit': 'Ma'}])
    return str(d)


def blank_to_empty_string(magic_df, cols):
    """Hold the blanks of cols as '' in object columns, as the GUIs do."""
    for col in cols:
        values = magic_df.df[col].astype(object)
        magic_df.df[col] = values.where(values.notnull(), '')


class TestContributionTables:

    def test_reads_the_tables_present(self, study):
        con = cb.Contribution(study)
        assert set(con.tables) == {'locations', 'sites', 'samples', 'specimens', 'ages'}
        assert len(con.tables['samples'].df) == 4

    def test_custom_filenames(self, study):
        os.rename(os.path.join(study, 'samples.txt'), os.path.join(study, 'my_samples.txt'))
        con = cb.Contribution(study, custom_filenames={'samples': 'my_samples.txt'})
        assert con.filenames['samples'] == 'my_samples.txt'
        assert len(con.tables['samples'].df) == 4

    def test_add_magic_table(self, study):
        """By dtype, by file name with the dtype read from the file, and failures."""
        con = cb.Contribution(study, read_tables=['specimens'])
        assert con.add_magic_table('samples')[0] == 'samples'
        dtype, sites = con.add_magic_table('unknown', 'sites.txt')
        assert dtype == 'sites'
        assert set(con.tables) == {'specimens', 'samples', 'sites'}
        assert con.add_magic_table('criteria') == (False, False)
        assert con.add_magic_table('not_a_table') == (False, False)

    def test_add_magic_table_from_data(self, study):
        """A measurements table is given a sequence number for each record."""
        con = cb.Contribution(study, read_tables=[])
        dtype, meas = con.add_magic_table_from_data('measurements', [
            {'measurement': 'm1', 'experiment': 'e1', 'specimen': 'a1', 'magn_moment': 1e-5},
            {'measurement': 'm2', 'experiment': 'e1', 'specimen': 'a1', 'magn_moment': 5e-6}])
        assert dtype == 'measurements'
        sequence = list(meas.df['sequence'])
        assert sequence == [sequence[0], sequence[0] + 1]

    def test_add_empty_magic_table(self, study):
        con = cb.Contribution(study, read_tables=['specimens'])
        con.add_empty_magic_table('samples')
        assert len(con.tables['samples'].df) == 0
        con.add_empty_magic_table('not_a_table')
        assert set(con.tables) == {'specimens', 'samples'}

    @pytest.mark.parametrize('table, expected', [
        ('measurements', ('specimens', None)),
        ('samples', ('sites', 'specimens')),
        ('locations', (None, 'sites')),
        ('ages', (None, None))])
    def test_get_parent_and_child(self, study, table, expected):
        con = cb.Contribution(study, read_tables=[])
        assert con.get_parent_and_child(table) == expected


class TestContributionMissingItems:

    @pytest.fixture
    def con(self, tmp_path):
        """Samples name a site s2 that is not in sites; specimens name a sample x not in samples."""
        write_table(tmp_path, 'sites', [{'site': 's1', 'location': 'L'}])
        write_table(tmp_path, 'samples', [{'sample': 'a', 'site': 's1'}, {'sample': 'b', 'site': 's2'}])
        write_table(tmp_path, 'specimens', [{'specimen': 'a1', 'sample': 'a'},
                                            {'specimen': 'x1', 'sample': 'x'}])
        return cb.Contribution(str(tmp_path))

    def test_find_missing_items(self, con):
        assert con.find_missing_items('sites') == {'s2'}
        assert con.find_missing_items('samples') == {'x'}
        assert con.find_missing_items('specimens') == set()

    def test_propagate_all_tables_info(self, con, tmp_path):
        """
        Missing items get a row in their own table, with the parent where it is
        known, and a missing locations table is made from sites; nothing is
        written when write=False.
        """
        con.propagate_all_tables_info(write=False)
        assert sorted(con.tables['sites'].df.index) == ['s1', 's2']
        assert sorted(con.tables['samples'].df.index) == ['a', 'b', 'x']
        assert con.tables['sites'].df.loc['s2', 'site'] == 's2'
        assert list(con.tables['locations'].df.index) == ['L']
        assert not os.path.exists(os.path.join(str(tmp_path), 'locations.txt'))
        for table in ['sites', 'samples']:
            assert con.find_missing_items(table) == set()

    def test_propagate_all_tables_info_writes_tables(self, con, tmp_path):
        con.propagate_all_tables_info()
        assert len(cb.MagicDataFrame(os.path.join(str(tmp_path), 'locations.txt')).df) == 1
        assert len(cb.MagicDataFrame(os.path.join(str(tmp_path), 'sites.txt')).df) == 2

    @pytest.mark.xfail(strict=True, reason="a child table made from a colon-delimited list "
                       "names every row after the table (child_name for c_name in "
                       "propagate_all_tables_info, which also tests the stale loop "
                       "variable 'children')")
    def test_child_table_from_a_list_of_names(self, tmp_path):
        write_table(tmp_path, 'sites', [{'site': 's1', 'location': 'L', 'samples': 'a:b'}])
        con = cb.Contribution(str(tmp_path))
        con.propagate_all_tables_info(write=False)
        samples = con.tables['samples'].df
        assert sorted(samples.index) == ['a', 'b']
        assert list(samples['site']) == ['s1', 's1']

    def test_children_from_a_list_of_names_fill_an_existing_table(self, tmp_path):
        write_table(tmp_path, 'sites', [{'site': 's1', 'location': 'L', 'samples': 'a:b'}])
        write_table(tmp_path, 'samples', [{'sample': 'a', 'site': 's1'}])
        con = cb.Contribution(str(tmp_path))
        con.propagate_all_tables_info(write=False)
        assert con.tables['samples'].df.loc['b', 'site'] == 's1'


class TestContributionPropagation:

    def test_get_min_max_lat_lon(self, tmp_path):
        """
        Location bounds from the site coordinates, with coordinates given as
        strings or missing, written to locations.txt.
        """
        sites = cb.MagicDataFrame(dtype='sites')
        sites.add_row('site1', {'lat': 10, 'lon': 4, 'location': 'location1'})
        sites.add_row('site2', {'lat': 10.2, 'lon': 5, 'location': 'location1'})
        sites.add_row('site3', {'lat': 20, 'lon': '15', 'location': 'location2'})
        sites.add_row('site4', {'lat': None, 'location': 'location1'})
        locations = cb.MagicDataFrame(dtype='locations', columns=['lat_n', 'lat_s', 'lon_e', 'lon_w'])
        locations.add_row('location1', {})
        locations.add_row('location2', {})
        con = cb.Contribution(str(tmp_path), read_tables=[])
        con.tables['sites'] = sites
        con.tables['locations'] = locations
        con.get_min_max_lat_lon()
        bounds = con.tables['locations'].df[['lat_s', 'lat_n', 'lon_w', 'lon_e']].astype(float)
        assert list(bounds.loc['location1']) == [10., 10.2, 4., 5.]
        assert list(bounds.loc['location2']) == [20., 20., 15., 15.]
        assert os.path.exists(os.path.join(str(tmp_path), 'locations.txt'))

    def test_propagate_average_up(self, study):
        """
        A blank site lat/lon is the mean of its samples; a site that has
        coordinates keeps them.
        """
        con = cb.Contribution(study, read_tables=['sites', 'samples'])
        con.propagate_average_up()
        coords = con.tables['sites'].df[['lat', 'lon']]
        assert list(coords.loc['s1']) == [15.0, 30.0]
        assert list(coords.loc['s2']) == [45.0, 10.0]
        assert not {'new_lat', 'new_lon'} & set(con.tables['sites'].df.columns)

    def test_propagate_average_up_cannot_run(self, study):
        """Tables that are not neighbours, or samples without a site column, change nothing."""
        con = cb.Contribution(study, read_tables=['sites', 'samples'])
        assert con.propagate_average_up(target_df_name='sites', source_df_name='specimens') is None
        assert con.propagate_average_up(target_df_name='samples', source_df_name='sites') is None
        del con.tables['samples'].df['site']
        sites = con.propagate_average_up()
        assert pd.isnull(sites.df.loc['s1', 'lat'])

    def test_propagate_cols_up(self, study):
        """
        A blank site value becomes the capitalized, sorted, colon-delimited
        list of its sample values; filled values are kept.
        """
        con = cb.Contribution(study, read_tables=['sites', 'samples'])
        blank_to_empty_string(con.tables['sites'], ['lithologies'])
        con.propagate_cols_up(['lithologies'], 'sites', 'samples')
        assert dict(con.tables['sites'].df['lithologies']) == \
            {'s1': 'Basalt:Diabase', 's2': 'Gabbro', 's3': 'Basalt'}

    @pytest.mark.xfail(strict=True, reason=NAN_IS_PRESENT)
    def test_propagate_cols_up_blank_from_file(self, study):
        con = cb.Contribution(study, read_tables=['sites', 'samples'])
        con.propagate_cols_up(['lithologies'], 'sites', 'samples')
        assert con.tables['sites'].df.loc['s1', 'lithologies'] == 'Basalt:Diabase'

    def test_propagate_cols_up_without_a_link(self, study):
        """Samples without a site column leave the sites table as it was."""
        con = cb.Contribution(study, read_tables=['sites', 'samples'])
        del con.tables['samples'].df['site']
        sites = con.propagate_cols_up(['lithologies'], 'sites', 'samples')
        assert pd.isnull(sites.df.loc['s1', 'lithologies'])
        assert sites.df.loc['s2', 'lithologies'] == 'Gabbro'

    def test_propagate_lithology_cols(self, study):
        """Blank sample and specimen lithology columns take the values of their site."""
        con = cb.Contribution(study, read_tables=['sites', 'samples', 'specimens'])
        blank_to_empty_string(con.tables['samples'], ['lithologies'])
        con.propagate_lithology_cols()
        samples = con.tables['samples'].df
        assert samples.loc['c', 'lithologies'] == 'Gabbro'
        assert samples.loc['b', 'lithologies'] == 'diabase:basalt'
        assert samples.loc['a', 'geologic_classes'] == 'Extrusive'
        specimens = con.tables['specimens'].df
        assert dict(specimens['geologic_types']) == {'a1': 'Lava Flow', 'c1': 'Intrusion'}

    @pytest.mark.xfail(PANDAS_3, strict=True, reason="under pandas 3 blank text cells are "
                       "read as NaN; " + NAN_IS_PRESENT)
    def test_propagate_lithology_cols_blank_from_file(self, study):
        con = cb.Contribution(study, read_tables=['sites', 'samples', 'specimens'])
        con.propagate_lithology_cols()
        assert con.tables['samples'].df.loc['c', 'lithologies'] == 'Gabbro'

    def test_propagate_min_max_up(self, study):
        """Location age bounds from its sites, without replacing a bound already given."""
        con = cb.Contribution(study, read_tables=['sites', 'locations'])
        con.propagate_min_max_up()
        locations = con.tables['locations'].df
        assert (locations.loc['L1', 'age_low'], locations.loc['L1', 'age_high']) == (100, 300)
        assert locations.loc['L2', 'age_high'] == 999
        con.propagate_min_max_up(min_suffix='lowest', max_suffix='highest')
        assert locations.loc['L1', 'age_lowest'] == 100
        assert con.propagate_min_max_up(source_df_name='samples') is None

    def test_get_age_levels(self, tmp_path):
        """An age belongs to the lowest level named in its row."""
        write_table(tmp_path, 'ages', [
            {'location': 'L', 'site': 's1', 'sample': '', 'specimen': '', 'age': 1},
            {'location': 'L', 'site': 's1', 'sample': 'a', 'specimen': '', 'age': 2},
            {'location': 'L', 'site': 's1', 'sample': 'a', 'specimen': 'a1', 'age': 3},
            {'location': 'L', 'site': '', 'sample': '', 'specimen': '', 'age': 4}])
        con = cb.Contribution(str(tmp_path), read_tables=['ages'])
        assert list(con.get_age_levels().df['level']) == ['site', 'sample', 'specimen', 'location']

    def test_propagate_ages(self, study):
        """
        Ages fill blank site ages without replacing ages already there, and
        the location bounds include them.
        """
        con = cb.Contribution(study)
        blank_to_empty_string(con.tables['sites'], ['age', 'age_unit'])
        con.propagate_ages()
        sites = con.tables['sites'].df
        assert dict(sites['age'].astype(float)) == {'s1': 100., 's2': 300., 's3': 50.}
        assert sites.loc['s3', 'age_unit'] == 'Ma'
        assert con.tables['locations'].df.loc['L2', 'age_low'] == 50

    @pytest.mark.xfail(strict=True, reason=NAN_IS_PRESENT)
    def test_propagate_ages_blank_from_file(self, study):
        con = cb.Contribution(study)
        con.propagate_ages()
        assert con.tables['sites'].df.loc['s3', 'age'] == 50


# ----------------------------------------------------------------------------
# module functions


@pytest.mark.parametrize('value, expected', [
    (1, True), (0, False), (True, True), (False, False),
    ('string', True), ('', False), (['a'], True), ([], False),
    (('t',), True), ((), False),
    (pd.DataFrame(['val1']), True), (pd.DataFrame([]), False),
    (pd.Series(['s']), True), (pd.Series([], dtype=object), False),
    (3., True), (np.nan, False), (None, False)])
def test_not_null(value, expected):
    assert cb.not_null(value) is expected


def test_not_null_zero_as_value():
    assert cb.not_null(0, zero_as_null=False)


def test_get_intensity_col():
    """magn_moment is preferred when it has data, otherwise the first filled column."""
    data = pd.DataFrame({'magn_volume': [1., 2.], 'magn_moment': [3., np.nan]})
    assert cb.get_intensity_col(data) == 'magn_moment'
    data['magn_moment'] = np.nan
    assert cb.get_intensity_col(data) == 'magn_volume'
    assert cb.get_intensity_col(data[[]]) == ''

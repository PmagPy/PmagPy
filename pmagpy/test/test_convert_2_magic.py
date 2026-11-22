"""
What every converter in convert_2_magic should do, whatever the format:

* return (False, message) for an input file that does not exist
* write its tables into the output directory and nowhere else, and not pick up
  tables lying in the working directory
* write MagIC 3 tables whose columns are in the data model (a column that is
  not, such as sample or site in a measurements table, is dropped on upload)
* reject a naming convention that needs a number of characters without one

The checks of the converted values for each format are in test_convert_demag.py,
test_convert_aniso.py, test_convert_rockmag.py and test_convert_iodp.py.
Tests marked xfail(strict=True) record known defects: they start to pass, and so
fail the suite, once the defect is fixed, which is the reminder to remove the mark.
"""
import os

import pytest

from pmagpy import convert_2_magic as convert
from pmagpy.test.convert_helpers import (CONVERT_DIR, convert_into, model_columns,
                                         read_table, table_type)


def in_dir(*parts):
    """the path of a directory in data_files/convert_2_magic"""
    return os.path.join(CONVERT_DIR, *parts)


# each converter as a function of (input file name, output directory), and the
# example file it is run on
CONVERTERS = {
    '_2g_bin': (lambda f, out: convert._2g_bin(mag_file=f, input_dir=in_dir('2g_bin_magic', 'mn1'),
                                               dir_path=out), 'mn001-1a.dat'),
    'agm': (lambda f, out: convert.agm(f, input_dir_path=in_dir('agm_magic'), dir_path=out,
                                       fmt='old'), 'agm_magic_example.agm'),
    'bgc': (lambda f, out: convert.bgc(f, input_dir_path=in_dir('bgc_magic'), dir_path=out),
            '96MT.05.01'),
    'generic': (lambda f, out: convert.generic(magfile=os.path.join(in_dir('generic_magic'), f),
                                               dir_path=out, experiment='Demag'),
                'generic_magic_example.txt'),
    'huji': (lambda f, out: convert.huji(magfile=f, input_dir_path=in_dir('huji_magic'),
                                         dir_path=out, codelist='AF'),
             'Massada_AF_HUJI_new_format.txt'),
    'huji_sample': (lambda f, out: convert.huji_sample(f, input_dir_path=in_dir('huji_magic'),
                                                       dir_path=out), 'magdelkrum_datafile.txt'),
    'jr6_txt': (lambda f, out: convert.jr6_txt(f, input_dir_path=in_dir('jr6_magic'), dir_path=out),
                'AP12.txt'),
    'jr6_jr6': (lambda f, out: convert.jr6_jr6(f, input_dir_path=in_dir('jr6_magic'), dir_path=out),
                'AF.jr6'),
    'k15': (lambda f, out: convert.k15(f, input_dir_path=in_dir('k15_magic'), dir_path=out),
            'k15_example.dat'),
    'kly4s': (lambda f, out: convert.kly4s(f, input_dir_path=in_dir('kly4s_magic'), dir_path=out),
              'KLY4S_magic_example.dat'),
    'ldeo': (lambda f, out: convert.ldeo(f, input_dir_path=in_dir('ldeo_magic'), dir_path=out,
                                         codelist='AF'), 'ldeo_magic_example.dat'),
    'livdb': (lambda f, out: convert.livdb(os.path.join(in_dir('livdb_magic'), f),
                                           output_dir_path=out), 'TH_IZZI+'),
    'mini': (lambda f, out: convert.mini(f, input_dir_path=in_dir('mini_magic'), dir_path=out,
                                         methcode='AF'), 'Peru_rev1.txt'),
    'mst': (lambda f, out: convert.mst(f, input_dir_path=in_dir('mst_magic'), dir_path=out),
            'curie_example.dat'),
    'pmd': (lambda f, out: convert.pmd(f, input_dir_path=in_dir('pmd_magic', 'UCSC', 'PMD'),
                                       dir_path=out), 'ss0207a.pmd'),
    's_magic': (lambda f, out: convert.s_magic(f, input_dir_path=in_dir('s_magic'), dir_path=out),
                's_magic_example.dat'),
    'sio': (lambda f, out: convert.sio(f, input_dir_path=in_dir('sio_magic'), dir_path=out,
                                       codelist='AF'), 'sio_af_example.dat'),
    'sufar4': (lambda f, out: convert.sufar4(f, input_dir_path=in_dir('sufar_asc_magic'),
                                             dir_path=out), 'sufar4-asc_magic_example.txt'),
    'utrecht': (lambda f, out: convert.utrecht(f, input_dir_path=in_dir('utrecht_magic'),
                                               dir_path=out), 'Utrecht_Example.af'),
}


def known_defect(names, reason):
    """
    The parameters for the converters in CONVERTERS, with a strict xfail mark
    on those that have the defect.

    Args:
        names (dict): converter name -> description of its defect
        reason (str): the expected behavior the defect breaks

    Returns:
        list: pytest parameters, one per converter
    """
    return [pytest.param(name, marks=pytest.mark.xfail(strict=True, reason='{}: {}'.format(
        reason, names[name]))) if name in names else name for name in CONVERTERS]


@pytest.mark.parametrize('name', known_defect({
    'huji_sample': 'raises FileNotFoundError',
    'jr6_jr6': 'raises FileNotFoundError',
    'jr6_txt': 'returns None',
    'livdb': 'raises FileNotFoundError',
    'utrecht': 'raises FileNotFoundError',
}, 'a missing input file should give (False, message)'))
def test_missing_input_file(name, tmp_path):
    """a missing input file gives (False, message), not an exception, and no tables"""
    call = CONVERTERS[name][0]
    result, out_dir, cwd = convert_into(tmp_path, lambda out: call('no_such_file.dat', out))
    assert isinstance(result, tuple)
    assert result[0] is False
    assert isinstance(result[1], str) and result[1]
    assert os.listdir(out_dir) == []


STALE = 'stale_table_entry'


@pytest.fixture(scope='module', params=list(CONVERTERS))
def converted(request, tmp_path_factory):
    """
    Each converter run on its example file, with a samples table from some
    earlier work left in the working directory.

    Returns:
        tuple: (converter name, result, output directory, working directory)
    """
    name = request.param
    call, filename = CONVERTERS[name]
    base = tmp_path_factory.mktemp(name.strip('_'))
    os.makedirs(os.path.join(str(base), 'cwd'))
    with open(os.path.join(str(base), 'cwd', 'samples.txt'), 'w') as f:
        f.write('tab\tsamples\nsample\tsite\n{0}\t{0}\n'.format(STALE))
    result, out_dir, cwd = convert_into(base, lambda out: call(filename, out))
    return name, result, out_dir, cwd


@pytest.mark.parametrize('converted', known_defect({
    'kly4s': 'writes samples.txt and sites.txt into the working directory',
    'mini': 'writes all of its tables into the working directory, not into dir_path',
}, 'a converter should only use its output directory'), indirect=True)
def test_uses_only_the_output_directory(converted):
    """nothing is written to, or read from, the working directory"""
    name, result, out_dir, cwd = converted
    assert os.listdir(cwd) == ['samples.txt']
    with open(os.path.join(cwd, 'samples.txt')) as f:
        assert STALE in f.read()
    for fname in os.listdir(out_dir):
        with open(os.path.join(out_dir, fname)) as f:
            assert STALE not in f.read(), fname


@pytest.mark.parametrize('converted', known_defect({
    'huji_sample': 'samples: location; sites: class, definition, lithology, type',
    'k15': 'measurements: experiments, location, sample, site; samples: location, specimen; '
           'specimens: location, site',
    'kly4s': 'measurements: location, sample, site; specimens: location, site',
    'mst': 'measurements: location, sample, site',
    's_magic': 'specimens: location, site',
}, 'every column should be in the MagIC 3 data model'), indirect=True)
def test_columns_are_in_the_data_model(converted):
    """every column of every table written is a column of that table in MagIC 3"""
    name, result, out_dir, cwd = converted
    extra = {}
    for fname in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, fname)
        table = table_type(path)
        columns = read_table(path).columns
        not_in_model = sorted(set(columns) - set(model_columns(table)))
        if not_in_model:
            extra[fname] = not_in_model
    assert extra == {}


WITH_NAMING_CONVENTION = {
    '_2g_bin': lambda con, out: convert._2g_bin(mag_file='mn001-1a.dat', samp_con=con, dir_path=out,
                                                input_dir=in_dir('2g_bin_magic', 'mn1')),
    'k15': lambda con, out: convert.k15('k15_example.dat', sample_naming_con=con, dir_path=out,
                                        input_dir_path=in_dir('k15_magic')),
    'kly4s': lambda con, out: convert.kly4s('KLY4S_magic_example.dat', samp_con=con, dir_path=out,
                                            input_dir_path=in_dir('kly4s_magic')),
    'sio': lambda con, out: convert.sio('sio_af_example.dat', samp_con=con, dir_path=out,
                                        input_dir_path=in_dir('sio_magic')),
    'sufar4': lambda con, out: convert.sufar4('sufar4-asc_magic_example.txt', sample_naming_con=con,
                                              dir_path=out, input_dir_path=in_dir('sufar_asc_magic')),
}


@pytest.mark.parametrize('name, con', [
    pytest.param('k15', '7', marks=pytest.mark.xfail(
        strict=True, reason='k15 does not check convention 7 and raises ValueError'))
    if (name, con) == ('k15', '7') else (name, con)
    for name in WITH_NAMING_CONVENTION for con in ('4', '7')])
def test_naming_convention_needs_a_number(name, con, tmp_path):
    """conventions 4 and 7 need the number of characters, as 4-Z or 7-Z"""
    call = WITH_NAMING_CONVENTION[name]
    result, out_dir, cwd = convert_into(tmp_path, lambda out: call(con, out))
    assert result[0] is False
    assert '{}-Z'.format(con) in result[1]
    assert os.listdir(out_dir) == []

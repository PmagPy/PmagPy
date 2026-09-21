"""
Tests for ipmag.aniso_magic and for the aniso_magic.py command-line program.

The site and sample selection parameters (sites, group_sites, isample, samples,
group_samples) were added to ipmag.aniso_magic for PmagPy/PmagPy#541. They
were inserted in the middle of the signature, and programs/aniso_magic.py
called the function with positional arguments, so every argument after isite
landed in the wrong parameter and the program raised a TypeError on every run.

aniso_magic also read its tables from dir_path but saved its plots in the
current directory, because dir_path was not passed on to save_plots.
"""
import inspect
import os
import shutil
import sys

import matplotlib
import matplotlib.pyplot as plt
import pytest

from pmagpy import ipmag

DATA_FILES = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'data_files')


def copy_tables(dataset, destination, names):
    """Copy MagIC tables from an example dataset to a scratch directory."""
    for name in names:
        shutil.copy(os.path.join(DATA_FILES, dataset, name), destination)


def plot_names(directory):
    return sorted(name for name in os.listdir(directory) if name.endswith('.png'))


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


@pytest.fixture
def scratch_dir(tmp_path, monkeypatch):
    """
    A directory for the tables and plots, with the tests run from a different,
    empty directory so that anything saved in the current directory instead of
    in dir_path is caught (and stays out of the repository).
    """
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    tables = tmp_path / 'tables'
    tables.mkdir()
    yield tables
    assert os.listdir(elsewhere) == []


@pytest.fixture
def atrm_dir(scratch_dir):
    # data_files/atrm_magic: 30 specimens with anisotropy tensors, one per
    # sample, in ten sites; sites ak01 and ak04 have four specimens each
    copy_tables('atrm_magic', scratch_dir, ['specimens.txt', 'samples.txt', 'sites.txt'])
    return str(scratch_dir)


@pytest.fixture
def aarm_dir(scratch_dir):
    # data_files/aarm_magic: six specimens with anisotropy tensors, all from
    # sample bg2 of location Bushveld
    copy_tables('aarm_magic', scratch_dir, ['specimens.txt', 'samples.txt', 'sites.txt'])
    return str(scratch_dir)


def hext_plots(dir_path, **kwargs):
    """Run aniso_magic with Hext ellipses only, which is quick."""
    return ipmag.aniso_magic(dir_path=dir_path, iboot=0, ihext=1, save_plots=True,
                             verbose=False, **kwargs)


class TestAnisoMagicSelection:

    def test_whole_file(self, atrm_dir):
        ok, saved = hext_plots(atrm_dir)
        assert ok
        assert plot_names(atrm_dir) == ['unknown_s_aniso-conf.png',
                                        'unknown_s_aniso-data.png']
        assert len(saved) == 2

    def test_plots_are_saved_in_dir_path(self, atrm_dir):
        # run from another directory (see scratch_dir); the plots belong with
        # the tables in dir_path, as for the other *_magic plotting functions
        assert os.path.realpath(os.getcwd()) != os.path.realpath(atrm_dir)
        ok, saved = hext_plots(atrm_dir)
        assert ok
        assert len(plot_names(atrm_dir)) == 2
        assert plot_names(os.getcwd()) == []

    def test_listed_sites_each_get_their_own_plots(self, atrm_dir):
        ok, saved = hext_plots(atrm_dir, sites=['ak01', 'ak04'])
        assert ok
        assert plot_names(atrm_dir) == ['unknown_ak01_s_aniso-conf.png',
                                        'unknown_ak01_s_aniso-data.png',
                                        'unknown_ak04_s_aniso-conf.png',
                                        'unknown_ak04_s_aniso-data.png']
        assert len(saved) == 4

    def test_single_site_given_as_a_string(self, atrm_dir):
        ok, saved = hext_plots(atrm_dir, sites='ak01')
        assert ok
        assert plot_names(atrm_dir) == ['unknown_ak01_s_aniso-conf.png',
                                        'unknown_ak01_s_aniso-data.png']

    def test_site_missing_from_the_data_is_skipped(self, atrm_dir):
        ok, saved = hext_plots(atrm_dir, sites=['ak01', 'not_a_site'])
        assert ok
        assert plot_names(atrm_dir) == ['unknown_ak01_s_aniso-conf.png',
                                        'unknown_ak01_s_aniso-data.png']

    def test_group_sites_pools_the_listed_sites_into_one_plot(self, atrm_dir):
        ok, saved = hext_plots(atrm_dir, sites=['ak01', 'ak04'], group_sites=True)
        assert ok
        assert plot_names(atrm_dir) == ['unknown_s_aniso-conf.png',
                                        'unknown_s_aniso-data.png']

    def test_group_samples_pools_the_listed_samples_into_one_plot(self, atrm_dir):
        ok, saved = hext_plots(atrm_dir, samples=['ak01a', 'ak01b', 'ak01c', 'ak01d'],
                               group_samples=True)
        assert ok
        assert plot_names(atrm_dir) == ['unknown_s_aniso-conf.png',
                                        'unknown_s_aniso-data.png']

    def test_listed_sample_gets_its_own_plots(self, aarm_dir):
        ok, saved = hext_plots(aarm_dir, samples=['bg2'])
        assert ok
        assert plot_names(aarm_dir) == ['Bushveld_bg2_s_aniso-conf.png',
                                        'Bushveld_bg2_s_aniso-data.png']

    def test_isample_iterates_over_all_samples(self, aarm_dir):
        ok, saved = hext_plots(aarm_dir, isample=True)
        assert ok
        assert plot_names(aarm_dir) == ['Bushveld_bg2_s_aniso-conf.png',
                                        'Bushveld_bg2_s_aniso-data.png']

    @pytest.mark.parametrize("conflict", [
        dict(isite=True, isample=True),
        dict(isite=True, sites=['ak01'], group_sites=True),
        dict(isample=True, samples=['ak01a'], group_samples=True),
    ])
    def test_conflicting_options_raise(self, atrm_dir, conflict):
        with pytest.raises(ValueError):
            hext_plots(atrm_dir, **conflict)

    def test_aniso_magic_nb_is_the_same_function(self):
        assert ipmag.aniso_magic_nb is ipmag.aniso_magic


@pytest.fixture(scope="module")
def program():
    # the program selects a GUI backend when it is imported (PmagPy/PmagPy#909),
    # so put back the one the test session is using
    backend = matplotlib.get_backend()
    from programs import aniso_magic
    matplotlib.use(backend, force=True)
    return aniso_magic


class TestAnisoMagicProgram:

    def test_arguments_reach_the_parameters_they_are_meant_for(self, program, monkeypatch):
        signature = inspect.signature(ipmag.aniso_magic)
        calls = []

        def record(*args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(program.ipmag, 'aniso_magic', record)
        monkeypatch.setattr(program.ipmag, 'aniso_magic_nb', record)
        monkeypatch.setattr(sys, 'argv', [
            'aniso_magic.py', '-WD', 'somewhere', '-f', 'my_specimens.txt',
            '-fsa', 'my_samples.txt', '-fsi', 'my_sites.txt', '-sit', '-par', '-v',
            '-crd', 'g', '-fmt', 'svg', '-n', '250', '-sav',
            '-gtc', '110', '2', '-d', '3', '290', '5'])
        program.main()

        assert len(calls) == 1
        args, kwargs = calls[0]
        # binding against the real signature is what catches arguments that
        # have drifted out of step with it
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        given = bound.arguments
        assert given['infile'] == 'my_specimens.txt'
        assert given['samp_file'] == 'my_samples.txt'
        assert given['site_file'] == 'my_sites.txt'
        assert given['dir_path'] == 'somewhere'
        assert given['isite'] == 1
        assert given['ipar'] == 1
        assert given['ivec'] == 1
        assert given['iboot'] == 1
        assert given['crd'] == 'g'
        assert given['fmt'] == 'svg'
        assert int(given['num_bootstraps']) == 250
        assert given['PDir'] == [110., 2.]
        assert given['vec'] == 2
        assert given['Dir'] == [290., 5.]
        assert given['save_plots'] is True
        assert given['interactive'] is False
        # the selection parameters added for #541 are not set from the
        # command line and must keep their defaults
        assert given['sites'] is None
        assert given['group_sites'] is False
        assert given['isample'] is False
        assert given['samples'] is None
        assert given['group_samples'] is False

    def test_runs_on_the_example_data(self, program, monkeypatch, scratch_dir):
        copy_tables('aniso_magic', scratch_dir, ['dike_specimens.txt'])
        monkeypatch.setattr(sys, 'argv', [
            'aniso_magic.py', '-WD', str(scratch_dir), '-f', 'dike_specimens.txt',
            '-B', '-sav'])
        program.main()
        assert plot_names(scratch_dir) == ['_g_aniso-conf.png', '_g_aniso-data.png']

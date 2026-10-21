"""
Tests for ipmag.load_magic_contribution.

The download from earthref.org is replaced by a copy of the MagIC
contribution 19340 file in data_files/download_magic, so the tests run
offline and can count how often the database would have been contacted.
"""
import os
import shutil

import pytest
import requests

from pmagpy import ipmag, pmag

CONTRIBUTION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_files",
    "download_magic", "magic_contribution_19340.txt")
MAGIC_ID = "19340"


@pytest.fixture
def fake_download(monkeypatch):
    """Replace download_magic_from_id with a local copy; record the calls."""
    calls = []

    def download(magic_id, directory='.', share_key=""):
        calls.append(magic_id)
        file_name = f'magic_contribution_{magic_id}.txt'
        shutil.copy(CONTRIBUTION_FILE, os.path.join(directory, file_name))
        return True, file_name

    monkeypatch.setattr(ipmag, 'download_magic_from_id', download)
    return calls


@pytest.fixture
def unpack_calls(monkeypatch):
    """Wrap unpack_magic to record the calls."""
    calls = []
    unpack_magic = ipmag.unpack_magic

    def unpack(*args, **kwargs):
        calls.append(args)
        return unpack_magic(*args, **kwargs)

    monkeypatch.setattr(ipmag, 'unpack_magic', unpack)
    return calls


def test_first_call_downloads_and_unpacks(tmp_path, fake_download, unpack_calls):
    contribution = ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert fake_download == [MAGIC_ID]
    assert len(unpack_calls) == 1
    assert (tmp_path / 'measurements.txt').exists()
    measurements = contribution.tables['measurements'].df
    assert len(measurements) > 0


def test_later_calls_use_the_local_copy(tmp_path, fake_download, unpack_calls):
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    contribution = ipmag.load_magic_contribution(int(MAGIC_ID),
                                                 dir_path=str(tmp_path))
    assert fake_download == [MAGIC_ID]
    assert len(unpack_calls) == 1
    assert 'measurements' in contribution.tables


def test_existing_file_is_unpacked_without_download(tmp_path, fake_download,
                                                    unpack_calls):
    shutil.copy(CONTRIBUTION_FILE, tmp_path / f'magic_contribution_{MAGIC_ID}.txt')
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert fake_download == []
    assert len(unpack_calls) == 1


def test_tables_of_another_contribution_are_replaced(tmp_path, fake_download,
                                                     unpack_calls):
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    # the unpacked tables now claim to belong to a different contribution
    contribution_table = tmp_path / 'contribution.txt'
    text = contribution_table.read_text()
    contribution_table.write_text(text.replace(MAGIC_ID, '99999'))
    contribution = ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert fake_download == [MAGIC_ID]
    assert len(unpack_calls) == 2
    assert [str(magic_id) for magic_id in
            contribution.tables['contribution'].df['id']] == [MAGIC_ID]


def test_leftover_tables_of_another_contribution_are_not_loaded(
        tmp_path, fake_download):
    # contribution 99999 left an images table; 19340 has none
    (tmp_path / 'contribution.txt').write_text(
        'tab delimited\tcontribution\nid\tversion\n99999\t1\n')
    (tmp_path / 'images.txt').write_text(
        'tab delimited\timages\nfile\tspecimen\nimage.png\tspecimen_1\n')
    contribution = ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert 'images' not in contribution.tables
    assert [str(magic_id) for magic_id in
            contribution.tables['contribution'].df['id']] == [MAGIC_ID]


def test_interrupted_unpack_is_completed(tmp_path, fake_download, unpack_calls):
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    # an interrupted unpack leaves contribution.txt, the first table written,
    # but not the tables after it
    for table in ['measurements', 'specimens', 'samples', 'sites']:
        (tmp_path / f'{table}.txt').unlink()
    contribution = ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert fake_download == [MAGIC_ID]
    assert len(unpack_calls) == 2
    assert len(contribution.tables['measurements'].df) > 0


def test_tables_of_another_version_are_replaced(tmp_path, fake_download,
                                                unpack_calls):
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    # the unpacked tables are from version 10; the file is version 11
    contribution_table = str(tmp_path / 'contribution.txt')
    records, _ = pmag.magic_read(contribution_table)
    records[0]['version'] = '10'
    pmag.magic_write(contribution_table, records, 'contribution')
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert fake_download == [MAGIC_ID]
    assert len(unpack_calls) == 2


def test_path_dir_path(tmp_path, fake_download):
    contribution = ipmag.load_magic_contribution(MAGIC_ID,
                                                 dir_path=tmp_path / 'data')
    assert len(contribution.tables['measurements'].df) > 0


def test_tables_in_contribution_file():
    tables, contribution_record = ipmag._magic_file_tables(CONTRIBUTION_FILE)
    assert tables == ['contribution', 'locations', 'sites', 'samples',
                      'specimens', 'measurements', 'criteria', 'ages']
    assert contribution_record['id'] == MAGIC_ID
    assert contribution_record['version'] == '11'


def test_overwrite_downloads_again(tmp_path, fake_download, unpack_calls):
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path), overwrite=True)
    assert fake_download == [MAGIC_ID, MAGIC_ID]
    assert len(unpack_calls) == 2


def test_creates_missing_directory(tmp_path, fake_download):
    dir_path = tmp_path / 'data' / 'contribution'
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(dir_path))
    assert (dir_path / 'measurements.txt').exists()


def test_failed_download_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(ipmag, 'download_magic_from_id',
                        lambda magic_id, directory='.', share_key="":
                        (False, 'Failed to download: Not Found'))
    with pytest.raises(RuntimeError, match='could not be downloaded'):
        ipmag.load_magic_contribution('0', dir_path=str(tmp_path))


def test_connection_error_raises(tmp_path, monkeypatch):
    """A network error in the real download_magic_from_id is a RuntimeError."""
    def no_connection(*args, **kwargs):
        raise requests.exceptions.ConnectionError('no network')

    monkeypatch.setattr(ipmag.requests, 'get', no_connection)
    with pytest.raises(RuntimeError, match='no network'):
        ipmag.load_magic_contribution(MAGIC_ID, dir_path=tmp_path)

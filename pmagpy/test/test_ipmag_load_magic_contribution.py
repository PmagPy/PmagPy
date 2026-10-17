"""
Tests for ipmag.load_magic_contribution.

The download from earthref.org is replaced by a copy of the MagIC
contribution 19340 file in data_files/download_magic, so the tests run
offline and can count how often the database would have been contacted.
"""
import os
import shutil

import pytest

from pmagpy import ipmag

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
    ipmag.load_magic_contribution(MAGIC_ID, dir_path=str(tmp_path))
    assert fake_download == [MAGIC_ID]
    assert len(unpack_calls) == 2


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

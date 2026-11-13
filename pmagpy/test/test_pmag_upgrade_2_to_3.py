"""
Tests for the upgrade of MagIC data model 2.5 tables to data model 3
(pmag.convert_directory_2_to_3 and pmag.convert_criteria_file_2_to_3), which
Pmag GUI's "convert 2.5 to 3.0" button runs. The 2.5 code of PmagPy is being
removed; these keep the upgrade path, which must stay, under test. The 2.5
tables are those of data_files/2_5/McMurdo.
"""
import os
import shutil

import pandas as pd

from pmagpy import pmag

MCMURDO = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "data_files", "2_5", "McMurdo")


def read(directory, table):
    return pd.read_csv(os.path.join(str(directory), table + ".txt"), sep="\t", header=1, dtype=str,
                       keep_default_na=False)


def test_a_directory_is_upgraded(tmp_path):
    meas, upgraded, not_upgraded = pmag.convert_directory_2_to_3(input_dir=MCMURDO, output_dir=str(tmp_path))
    assert sorted(upgraded) == sorted(["measurements.txt", "specimens.txt", "samples.txt", "sites.txt",
                                       "locations.txt", "criteria.txt", "ages.txt"])
    assert sorted(not_upgraded) == sorted(["pmag_results.txt", "rmag_hysteresis.txt", "rmag_anisotropy.txt",
                                           "rmag_results.txt", "er_images.txt"])
    measurements = read(tmp_path, "measurements")
    assert len(measurements) > 0 and {"specimen", "method_codes", "treat_temp"} <= set(measurements.columns)
    # the columns with a data model 3 name are renamed (columns without one, e.g. measurement_loop_n, are
    # kept as they are)
    assert not {"er_specimen_name", "magic_method_codes", "measurement_temp", "measurement_dec"} & set(measurements)
    # the specimens, samples and sites hang together
    specimens, samples, sites = read(tmp_path, "specimens"), read(tmp_path, "samples"), read(tmp_path, "sites")
    assert set(specimens["sample"]) <= set(samples["sample"])
    assert set(samples["site"]) <= set(sites["site"])
    # the 2.5 tables are left as they were
    assert os.path.isfile(os.path.join(MCMURDO, "magic_measurements.txt"))


def test_the_criteria_are_upgraded(tmp_path):
    outfile, criteria = pmag.convert_criteria_file_2_to_3(input_dir=MCMURDO, output_dir=str(tmp_path))
    assert outfile == "criteria.txt"
    df = read(tmp_path, "criteria")
    assert len(df) and {"criterion", "table_column", "criterion_value"} <= set(df.columns)
    assert all("." in value for value in df["table_column"])         # e.g. specimens.dir_mad_free


def test_the_source_folder_is_not_changed(tmp_path):
    source = tmp_path / "McMurdo"
    shutil.copytree(MCMURDO, source)
    before = sorted(os.listdir(source))
    pmag.convert_directory_2_to_3(input_dir=str(source), output_dir=str(tmp_path / "out"))
    assert sorted(os.listdir(source)) == before

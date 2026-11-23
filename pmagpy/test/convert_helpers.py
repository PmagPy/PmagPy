"""
Helpers shared by the tests of the convert_2_magic converters.

Each converter is run from an empty working directory and writes into a
separate empty output directory, so that a converter that writes to, or reads
from, the working directory instead of its output directory is caught, and
nothing is ever written into data_files.
"""
import contextlib
import io
import os

import pandas as pd

from pmagpy import data_model3

WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
CONVERT_DIR = os.path.join(WD, 'data_files', 'convert_2_magic')


def convert_into(base_dir, call):
    """
    Run a converter with an output directory and an empty working directory.

    Args:
        base_dir (pathlib.Path): an empty temporary directory; the
            subdirectories 'out' and 'cwd' are made in it
        call (callable): takes the output directory (str) and runs the
            converter with it, returning the converter's result

    Returns:
        tuple: (the converter's result, the output directory, the working
            directory the converter ran from)
    """
    out_dir = os.path.join(str(base_dir), 'out')
    cwd = os.path.join(str(base_dir), 'cwd')
    os.makedirs(out_dir)
    os.makedirs(cwd, exist_ok=True)
    start = os.getcwd()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            result = call(out_dir)
    finally:
        os.chdir(start)
    return result, out_dir, cwd


def read_table(path):
    """
    Read a MagIC 3 table as written, without any of the conversions that
    contribution_builder applies.

    Args:
        path (str): a tab-delimited MagIC file, or a directory together with
            the table name, e.g. os.path.join(out_dir, 'measurements.txt')

    Returns:
        pandas.DataFrame: one row per record
    """
    return pd.read_csv(path, sep='\t', header=1)


def table_type(path):
    """
    The table type (measurements, specimens, ...) on the first line of a
    MagIC file.

    Args:
        path (str): a tab-delimited MagIC file

    Returns:
        str: the table type
    """
    with open(path) as f:
        return f.readline().split('\t')[1].strip()


_MODEL_COLUMNS = {}


def model_columns(table):
    """
    The columns of a table in the MagIC 3 data model.

    Args:
        table (str): table name, e.g. 'specimens'

    Returns:
        pandas.Index: the column names
    """
    if not _MODEL_COLUMNS:
        with contextlib.redirect_stdout(io.StringIO()):
            dm = data_model3.DataModel().dm
        _MODEL_COLUMNS.update({name: frame.index for name, frame in dm.items()})
    return _MODEL_COLUMNS[table]

"""
Rebuild this directory's measurements table from PmagPy's raw FORC example.

    python make_example.py

``data_files/forc_diagram/conventional_example.forc`` (a MicroMag AGM file
of 120 reversal curves, shipped with PmagPy's ``forc_diagram.py`` since 2018)
is written as a MagIC measurements table by
``pmagpy.forc.export_magic_measurements_from_raw``; the columns the export
leaves empty are dropped and the numbers are written with 10 significant
digits (the instrument wrote 7). The measurement timestamp is the one in the
file's header.
"""
import os

import pandas as pd

from pmagpy import forc

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "..", "forc_diagram", "conventional_example.forc")


def main():
    written = forc.export_magic_measurements_from_raw(RAW, out_dir=HERE, filename="measurements.txt",
                                                      specimen="conventional_example",
                                                      timestamp="2016-04-13T13:20:00")
    measurements = pd.read_csv(written, sep="\t", header=1)
    measurements = measurements.dropna(axis=1, how="all")
    # per-row constants that only repeat this file's provenance (the README has it)
    measurements = measurements.drop(columns=["citations", "files"])
    with open(written, "w") as fh:
        fh.write("tab \tmeasurements\n")
        # the instrument wrote 7 significant digits; 10 keep them without the
        # 17-digit repr the exporter uses to round-trip a double exactly
        measurements.to_csv(fh, sep="\t", index=False, float_format="%.10g")
    print(f"measurements: {len(measurements)} rows, {measurements.shape[1]} columns")


if __name__ == "__main__":
    main()

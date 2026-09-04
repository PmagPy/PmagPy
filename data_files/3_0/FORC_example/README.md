# FORC_example

A first-order reversal curve run as a MagIC measurements table, used as
example data for the FORC view of the PmagPy rock magnetism app and its tests.

The measurements are PmagPy's own raw FORC example,
`data_files/forc_diagram/conventional_example.forc` — a MicroMag 2900/3900
AGM file (Series 0015, measured 2016-04-13) of 120 reversal curves, with a
diagram window of B<sub>u</sub> ±0.1 T by B<sub>c</sub> 0–0.1 T and a
0.235 T calibration field in its header, shipped with the `forc_diagram.py`
program since 2018. Where the sample came from is not
recorded with the file.

| table | rows | content |
| --- | --- | --- |
| `measurements.txt` | 8514 | one `LP-FORC` experiment of specimen `conventional_example`: 120 calibration points and 120 curves, `meas_field_dc` (T) and `magn_moment` (Am²) |

The table is what `pmagpy.forc.export_magic_measurements_from_raw` writes,
with its empty columns dropped; the `measurement` names
(`LP-FORC-conventional_example-<curve>-<point>`, point 0 the calibration
measurement) carry the block structure the FORC pipeline needs to recover the
drift record. There are no specimens/samples/sites tables because nothing is
known about the sample. `make_example.py` rebuilds the table from the raw file.

# ThellierTool files from SE Poland

Unmodified copies from: Nawrocki, J. (2023). *Files containing data from each sample studied and ready to be open in Thellier Tool 4.0 software* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7994232 (CC BY 4.0). They are in a folder of their own, so that the tests that convert the whole `tdt_magic` folder leave them out.

| File | What it exercises |
| --- | --- |
| `BIE2A.tdt` | the MT4 protocol of ThellierTool: each pTRM tail check (`200.13` to `600.13`) follows an additivity check (`.14`), not the in-field step at its temperature. The five tail checks are `LT-PTRM-MD`. |
| `BOA3A.tdt` | the fields are separated by tabs, and in four data rows the moment field holds two values separated by a space (`4.116564E-02 1` at 600 °C). Split on spaces, such a row puts `1` in the declination and the declination in the inclination; `convert_2_magic.tdt` stops with a message naming the field instead. Nine of the 199 files of the archive have such rows (45 rows). |

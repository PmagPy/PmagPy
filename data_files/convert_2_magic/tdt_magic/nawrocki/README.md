# A ThellierTool file from SE Poland

`BOA3A.tdt`, an unmodified copy from: Nawrocki, J. (2023). *Files containing data from each sample studied and ready to be open in Thellier Tool 4.0 software* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7994232 (CC BY 4.0). It is in a folder of its own, so that the tests that convert the whole `tdt_magic` folder leave it out.

What it exercises: the fields are separated by tabs, and in four data rows the moment field holds two values separated by a space (`4.116564E-02 1` at 600 °C). Split on spaces, such a row puts `1` in the declination and the declination in the inclination. `convert_2_magic.tdt` stops with a message naming the field instead. Nine of the 199 files of the archive have such rows (45 rows).

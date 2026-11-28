# 2G tab-delimited exports (.DAT) of Han et al. (2022)

Test files for `convert_2_magic._2g_tab`: tab-delimited exports of the 2G Enterprises magnetometer software, with a header row of column names. These files have 12 columns (`Sample ID`, `Declination: Unrotated`, `Inclination: Unrotated`, `Intensity`, `X corr`, `Y corr`, `Z corr`, `X drift`, `Y drift`, `Z drift`, `Temp C`, `Sample Timestamp`): directions in specimen coordinates, thermal steps, no volume and no orientation. According to the ReadMe of the archive, the intensity is in emu; the `X/Y/Z corr` components give the `Intensity` column (the moment, as no volume was set).

The files are unmodified copies from the archive (folder `Thermal Demag RawData/Juanlingcao section`, and `Dongbeigou section` for `SYDBG4G-2-1.DAT`).

| File | What it tests |
| --- | --- |
| `SYJLC3-29.DAT` | line 17 holds two rows (585 and 600 °C) with the line break between them missing, which are split; two NRM rows and three rows at 80 °C |
| `SYTJG5-205.DAT` | line 4 is an interrupted measurement (9 of 12 fields), repeated on line 5 |
| `SYJLCK-4.DAT` | the specimen is named `SYJLCk-4` in some rows and `SYJLCK-4` in others |
| `SYTJG5-179.DAT`, `SYTJG5-179 .DAT` | one specimen in two files (to 400 °C, and an NRM and 450 °C on; `Sample ID` with a trailing space in the second), ordered by their timestamps; a row with `Temp C` NA, 11 minutes before the 400 °C row (`untreated`) |
| `SYDBG4G-2-1.DAT` | the 620 °C row (line 16, a run of 07/20/20) whose declination, inclination and intensity are not those of its `X/Y/Z corr` components (26° apart): the columns are entered as one set |

## Source

Han, F., Wang, Q., Wang, H., Zhu, X., Zhou, X., Wang, Z., Fang, K., Stidham, T. A., Wang, W., Wang, X., Li, X., Qin, H., Fan, L., Wen, C., Luo, J., Pan, Y., & Deng, C. (2022). Data for Han et al., 2022, PNAS, "Low dinosaur biodiversity in central China 2 million years prior to the end-Cretaceous mass extinction" [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7025078. License: CC BY 4.0.

The data of Han, F., Wang, Q., Wang, H., Zhu, X., Zhou, X., Wang, Z., Fang, K., Stidham, T. A., Wang, W., Wang, X., Li, X., Qin, H., Fan, L., Wen, C., Luo, J., Pan, Y., & Deng, C. (2022). Low dinosaur biodiversity in central China 2 million years prior to the end-Cretaceous mass extinction. *Proceedings of the National Academy of Sciences*, 119(39), e2211234119. https://doi.org/10.1073/pnas.2211234119

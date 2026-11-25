# PMD files from the Ivrea-Verbano Zone

Three PMD files, unmodified copies from:

Siravo, G., & Speranza, F. (2024). *Magnetic and paleomagnetic data from the Ivrea-Verbano Zone* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.15101810 (CC BY 4.0), for Siravo, G., Speranza, F., Minelli, L., Zucali, M., Fazio, E., Caricchi, C., & Spagnuolo, L. (2025), Magnetic and paleomagnetic characterization of the Ivrea-Verbano lower crust body (NW Italy): assessing the magnetization of Variscan-age lower crust, *Journal of Geophysical Research: Solid Earth*, 130(6), e2024JB031017, https://doi.org/10.1029/2024JB031017

The archive holds 426 such files (4,524 steps) in the folders `ossola_AF`, `strona_AF` and `termico` of `paleomag_data.zip`; the files here keep those folder names, since the same specimen name occurs in more than one folder.

| File | What it exercises |
| --- | --- |
| `ossola_AF/IVB0101.pmd` | steps `0mT` to `100mT`; the label `100mT` runs into the first number (`100mT-4.46E-10`); no date after the volume |
| `strona_AF/IVB2401.pmd` | moments rounded up to `10.00E-10` and `10.00E-09` |
| `termico/IVB0102.pmd` | steps labelled `2mT` to `68mT` in the folder of thermal demagnetizations; used to test that `dmg` sets the type of every step |

The geographic and tilt-corrected directions stored in the files are reproduced with azimuth = `a`, dip = −`b`, bedding dip direction = `s` + 90 and bedding dip = `d`.

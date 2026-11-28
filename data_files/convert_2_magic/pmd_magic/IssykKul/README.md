# PMD files from the Issyk-Kul Basin

Three PMD files, unmodified copies from:

Roud, S. C., Wack, M. R., Gilder, S. A., Kudriavtseva, A., & Sobel, E. (2021). *Rock magnetic, paleomagnetic and stratigraphic data of Cenozoic sediments from the Issyk-Kul Basin, central Tian Shan* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.4548968 (CC BY 4.0), for Roud, S. C., Wack, M. R., Gilder, S. A., Kudriavtseva, A., & Sobel, E. R. (2021), Miocene to early Pleistocene depositional history and tectonic evolution of the Issyk-Kul Basin, central Tian Shan, *Geochemistry, Geophysics, Geosystems*, 22(4), e2020GC009556, https://doi.org/10.1029/2020GC009556

The archive holds 430 such files (6,582 steps) in four folders; the files here come from three of them.

| File | Folder in the archive | What it exercises |
| --- | --- | --- |
| `A001.pmd` | `AT_AFdemag` | a PaleoMac export ("Output from PaleoMac"): carriage returns alone as line ends; `V=` in upper case without `m3`, followed by `strati=` instead of a date; a second header line (`Slat=`, `Slon=`, `Strati pos.=`, ...); steps `N000`, `A002`, ... (alternating field, mT); moments with two significant digits; a hade `b` of 97° |
| `S001.pmd` | `KS_AFdmag` | the same layout, with an azimuth of 363° |
| `AT036.pmd` | `AT_THRMdemag` | the usual PMD layout with Windows line ends; steps `N000`, `T150`, ... (thermal, °C); a hade of 101.5°; the first line holds the site coordinates |

The geographic and tilt-corrected directions stored in the files are reproduced with azimuth = `a`, dip = −`b`, bedding dip direction = `s` + 90 and bedding dip = `d`.

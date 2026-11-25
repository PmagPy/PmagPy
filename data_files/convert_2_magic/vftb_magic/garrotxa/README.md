# VFTB files from La Garrotxa

Unmodified copies from: Vernet Tarragó, E. (2026). *Raw data of La Garrotxa Volcanic Field (NE Iberia) Pleistocene lava-flows* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.20326424 (CC BY 4.0), for Vernet et al. (2026), *Geologica Acta*, 24.15, https://doi.org/10.1344/GeologicaActa2026.24.15. They are in a folder of their own, so that tests reading `vftb_magic` leave them out.

| File | Curve | What it exercises |
| --- | --- | --- |
| `GTX0208B.coe` | back-field demagnetization of the IRM | the curve starts at zero field (`rockmag.process_backfield_data`) |
| `GTX0208B.hys` | hysteresis loop | the file begins with the initial magnetization curve, from -8.37 mT to the peak field, before the two branches (`rockmag.process_hyst_loop`) |
| `GTX0308B_500.rmp` | magnetization against temperature in about 35 mT, heated to 499 °C (500 in the file name) and cooled (a thermal-stability cycle) | measured at temperature in the field: `meas_temp`, `meas_field_dc` |
| `OLO106_250.rmp` | a thermal-stability cycle to 251 °C whose field column is -999 on every line (the field was not recorded; 11 of the 46 cycles of the archive) | -999 is the missing value of the VFTB software: `meas_field_dc` is left empty |

# Remasoft .rs3 example files

Demagnetization data in the format of Remasoft (Chadima and Hrouda, 2006), one specimen per file, for `convert_2_magic.rs3` and its tests. The files are unmodified copies from three Zenodo datasets and one figshare dataset, all licensed CC BY 4.0. The files in `garrotxa/` and `svalbard/` are in folders of their own, so that the tests that convert the whole folder leave them out (`OL01-2B.rs3` needs `m_rows`, and the two GTX08 files share a specimen name).

| File | Source | What it exercises |
| --- | --- | --- |
| `PRG2-1C.rs3` | Praia Grande | alternating field steps; orientation with P2 = 90; an anchored line (CA) and a free line from the NRM (CB) |
| `PRG1-6B.rs3` | Praia Grande | thermal steps; an anchored line with limits in °C |
| `PRG6-2A.rs3` | Praia Grande | one thermal step followed by alternating field steps; the stored fit used all 16 steps although its first limit reads 2 mT |
| `PRG7-8A.rs3` | Praia Grande | a step measured twice (30 mT) |
| `BO14-9-3.rs3` | Bolnisi | thermal steps; orientation with P2 = 0; no stored fits |
| `BO6-6-3.rs3` | Bolnisi | free and anchored lines and a great circle; component names with spaces |
| `garrotxa/OL01-2B.rs3` | La Garrotxa | steps with ID M and no unit in the heading of the step column (`Step[]`), thermal according to the paper; fit limits without a unit |
| `garrotxa/GTX080101A.rs3`, `garrotxa/GTX080102A.rs3` | La Garrotxa | thermal steps; the specimen name in both files is `GTX08010`, the first 8 characters of the file names |
| `garrotxa/GTX0105A.rs3` | La Garrotxa | a line flagged O whose stored direction and MAD are those of the line anchored to the origin |
| `svalbard/amf1201.rs3` | NE Svalbard | a line flagged O whose stored direction and MAD are those of the free line with the origin added as a point |

## Sources

- Praia Grande (São Vicente, Cape Verde): Calvo-Rathert, M., Carrancho, Á., Morales, J., Pérez, N., & Caccavari, A. (2021). Rock-magnetic, paleomagnetic and multimethod paleointensity data from an upper Miocene lava flow sequence from São Vicente (Cape Verde) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.5553392
- Bolnisi (Georgia): the dataset cited in Calvo-Rathert et al. (2021), *Journal of Geophysical Research: Solid Earth*, 126, e2020JB020019, https://doi.org/10.1029/2020JB020019, as https://doi.org/10.5281/zenodo.3997235
- La Garrotxa (NE Iberia): Vernet Tarragó, E. (2026). Raw data of La Garrotxa Volcanic Field (NE Iberia) Pleistocene lava-flows [Data set]. Zenodo. https://doi.org/10.5281/zenodo.20326424, for Vernet, E., Calvo-Rathert, M., Beamud, E., Bógalo, M.-F., Carrancho, Á., Planagumà, L., & Martí, J. (2026), *Geologica Acta*, 24, 1–18, https://doi.org/10.1344/geologicaacta2026.24.15
- NE Svalbard: Michalski, K., Manby, G. M., Nejbert, K., & Domańska-Siuda, J. Palaeomagnetic investigations across Hinlopenstretet border zone: from Caledonian metamorphosed rocks of Ny Friesland to foreland facies of Nordaustlandet (NE Svalbard) [Data set]. figshare. https://doi.org/10.6084/m9.figshare.21641594.v1

Remasoft: Chadima, M., & Hrouda, F. (2006). Remasoft 3.0 a user friendly paleomagnetic data browser and analyzer. *Travaux Géophysiques*, XXVII, 20–21.

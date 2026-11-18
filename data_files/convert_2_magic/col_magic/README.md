# Paleomagnetism.org collection files (.col)

Test files for `convert_2_magic.col`. A `.col` file is the JSON file that the interpretation portal of [Paleomagnetism.org](https://paleomagnetism.org) 2 saves: for each specimen the demagnetization steps in specimen coordinates (µA/m), the core and bedding orientation, position, age, geology and lithology, and the line and plane fits made in the program, each in specimen, geographic and tectonic coordinates.

| File | Source | What it tests |
| --- | --- | --- |
| `28E.col` | Montheil (2023), unmodified | 4 alternating field specimens without a volume (`magn_volume` only), hidden steps, free and anchored lines, a specimen without fits, a core dip of -5 (MagIC dip -95) |
| `21E.col` | Montheil (2023), unmodified | 2 specimens without a demagnetization type, whose step labels are plain numbers |
| `NE02-Circ_subset.col` | Pastor-Galán and Boschman (2026), file `NE02-Circ.col`, reduced to 6 of its 79 specimens (NE2.1A, NE2.14, NE2.17, NE2.11A, NE2.11B, NE2.12) and without the `hash` field | specimens with a volume (`magn_moment` and `magn_volume`), thermal and alternating field specimens, an anchored plane that leaves out a step inside its range, a plane fitted to a mean direction (with its fitted line), bedding, two geologic classes and lithologies in one collection |

The tests also write changed copies of these files for what they do not hold: step labels with units, an unreadable label, assumed volumes, the Utrecht moments of Paleomagnetism.org 2.0.0–2.0.1, a hidden repeat of a step, two fits of one component, and copies of a specimen.

Sources (both CC BY 4.0):

- Montheil, L. (2023). NE Caribbean paleomagnetic dataset [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7791447. Data of Montheil, L., Philippon, M., Münch, P., Camps, P., Vaes, B., Cornée, J.-J., Poidras, T., & van Hinsbergen, D. J. J. (2023). Paleomagnetic rotations in the northeastern Caribbean region reveal major intraplate deformation since the Eocene. *Tectonics*, 42, e2022TC007706. https://doi.org/10.1029/2022TC007706
- Pastor-Galán, D., & Boschman, L. (2026). Paleomagnetic dataset from Maastrichtian-Paleocene rocks of the Nemuro arc, Hokkaido Japan [Data set]. Zenodo. https://doi.org/10.5281/zenodo.19704052

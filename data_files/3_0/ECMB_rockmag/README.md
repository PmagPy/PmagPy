# ECMB_rockmag

The rock-magnetic subset of MagIC contribution **20213** — the East Central
Minnesota Batholith (ECMB) study of Swanson-Hysell et al. (2021), *Tectonics*,
doi:10.1029/2021TC006751 — used as example data for the hysteresis and
backfield views of the PmagPy rock magnetism app and their tests.

The full contribution is mostly paleomagnetic directional data (AF and thermal
demagnetization of ~340 specimens). This directory keeps only the five
specimens with rock-magnetic experiments, and only those experiments:

| method codes | experiments | specimens |
| --- | --- | --- |
| `LP-HYS` (VSM hysteresis loops, ±1 T) | 5 | NED1-5c, NED2-8c, NED4-1c, NED6-6c, NED18-2c |
| `LP-BCR-BF` (VSM backfield curves) | 3 | NED1-5c, NED2-8c, NED18-2c |
| `LP-FC`, `LP-ZFC`, `LP-CW-SIRM:LP-MC`, `LP-CW-SIRM:LP-MW` (MPMS, 10–300 K) | 12 | NED2-8c, NED4-1c, NED18-2c |

The specimens, samples, sites and locations tables are filtered to the same
specimens; the contribution table is unchanged. Columns that are empty in the
kept rows were dropped from the measurements table. Nothing was edited
otherwise, so the numbers are those published in MagIC.

`make_subset.py` rebuilds the directory from an unpacked copy of the
contribution; MagIC keeps the authoritative copy at
https://earthref.org/MagIC/20213.

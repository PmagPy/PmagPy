"""
Rebuild this directory from an unpacked copy of MagIC contribution 20213.

    python make_subset.py /path/to/ECMB_unpacked

The source directory holds the contribution's MagIC tables as separate files
(contribution.txt, locations.txt, ..., measurements.txt), as ``download_magic``
writes them. The rows of the specimens with rock-magnetic experiments
(hysteresis, backfield, MPMS) are kept; the paleomagnetic directional data,
which is most of the contribution, is dropped along with the columns that are
empty in what remains.
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROCKMAG_CODES = ("LP-HYS", "LP-BCR", "LP-FC", "LP-ZFC", "LP-CW-SIRM", "LP-MW", "LP-MC")


def read(source, table):
    return pd.read_csv(os.path.join(source, f"{table}.txt"), sep="\t", header=1, dtype=str)


def write(table, df):
    df = df.dropna(axis=1, how="all")
    with open(os.path.join(HERE, f"{table}.txt"), "w") as fh:
        fh.write(f"tab \t{table}\n")
        df.to_csv(fh, sep="\t", index=False)
    print(f"{table}: {len(df)} rows, {df.shape[1]} columns")


def main(source):
    measurements = read(source, "measurements")
    codes = measurements["method_codes"].fillna("")
    is_rockmag = codes.apply(lambda s: any(code in s for code in ROCKMAG_CODES))
    measurements = measurements[is_rockmag]
    specimens_kept = measurements["specimen"].unique()

    specimens = read(source, "specimens")
    specimens = specimens[specimens["specimen"].isin(specimens_kept)]
    samples = read(source, "samples")
    samples = samples[samples["sample"].isin(specimens["sample"].unique())]
    sites = read(source, "sites")
    sites = sites[sites["site"].isin(samples["site"].unique())]
    locations = read(source, "locations")
    locations = locations[locations["location"].isin(sites["location"].unique())]

    write("contribution", read(source, "contribution"))
    write("locations", locations)
    write("sites", sites)
    write("samples", samples)
    write("specimens", specimens)
    write("measurements", measurements)


if __name__ == "__main__":
    main(sys.argv[1])

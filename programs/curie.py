#!/usr/bin/env python
"""Estimate Curie temperatures from a two-column temperature/data file."""

import argparse
import os

import numpy as np

from pmagpy import rockmag


METHODS = (
    "inflection",
    "max_curvature",
    "two_tangent",
    "inverse_susceptibility",
    "landau",
    "ms_squared_extrapolation",
)


def _estimate(T, y, method, window, t_range):
    if method in ("inflection", "max_curvature"):
        result = rockmag.curie_derivative_estimates(
            T, y, t_range=t_range, smooth_window=window
        )
        key = "inflection_temp" if method == "inflection" else "max_curvature_temp"
        return result[key]
    if method == "two_tangent":
        return rockmag.curie_two_tangent(T, y)["curie_temp"]
    if method == "inverse_susceptibility":
        return rockmag.curie_inverse_susceptibility(T, y)["curie_temp"]
    if method == "landau":
        return rockmag.curie_landau_fit(T, y, temp_unit="C")["curie_temp"]
    if method == "ms_squared_extrapolation":
        return rockmag.curie_Ms_squared_extrapolation(T, y)["curie_temp"]
    raise ValueError(f"Unknown Curie estimation method: {method}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Estimate a Curie temperature from a two-column text file."
    )
    parser.add_argument(
        "-f", required=True,
        help="input file containing temperature and data columns",
    )
    parser.add_argument(
        "-w", "--smooth-window", type=float, default=3,
        help="smoothing window in temperature units (default: 3)",
    )
    parser.add_argument(
        "-t", nargs=2, type=float, metavar=("MIN", "MAX"),
        help="temperature range to analyze",
    )
    parser.add_argument(
        "--method", choices=METHODS, default="max_curvature",
        help="Curie estimator (default: max_curvature)",
    )
    parser.add_argument(
        "-sav", action="store_true",
        help="save the diagnostic plot and exit",
    )
    parser.add_argument(
        "-fmt", default="svg",
        help="saved figure format (default: svg)",
    )
    args = parser.parse_args(argv)

    if not os.path.isfile(args.f):
        parser.error(f"input file not found: {args.f}")

    try:
        T, y = np.loadtxt(args.f, dtype=float, unpack=True)
    except (OSError, ValueError) as error:
        parser.error(f"could not read two numeric columns from {args.f}: {error}")

    T = np.atleast_1d(T)
    y = np.atleast_1d(y)
    finite = np.isfinite(T) & np.isfinite(y)
    T, y = T[finite], y[finite]
    if T.size < 4:
        parser.error("at least four finite temperature/data pairs are required")

    t_range = tuple(args.t) if args.t else None
    if t_range is not None:
        if t_range[0] >= t_range[1]:
            parser.error("temperature range minimum must be less than maximum")
        in_range = (T >= t_range[0]) & (T <= t_range[1])
        T, y = T[in_range], y[in_range]
        if T.size < 4:
            parser.error("temperature range must contain at least four finite pairs")

    estimate = _estimate(T, y, args.method, args.smooth_window, t_range)
    print(f"{args.method} Curie temperature: {estimate}")

    if args.sav:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot(T, y, "k-")
        if np.isfinite(estimate):
            ax.axvline(estimate, color="r", linestyle="--")
        ax.set_xlabel("Temperature")
        ax.set_ylabel("Magnetic signal")
        ax.set_title(f"Curie temperature: {args.method}")
        output = f"curie_{args.method}.{args.fmt}"
        fig.savefig(output)
        plt.close(fig)


if __name__ == "__main__":
    main()
"""
Publication-quality matplotlib figures for PmagPy Intensity.

Every function here takes plain core objects and returns a
``matplotlib.figure.Figure``, so the figures can be made from a notebook or a
script without starting the application:

    from pmagpy import paleointensity as pint
    from programs.pmagpy_intensity import publication as pub
    data = pint.PintData.from_directory("data_files/3_0/Megiddo")
    data.import_from_specimens_table()
    fig = pub.specimen_figure(data.specimens["hz05a1"], (0, 10),
                              data.statistics("hz05a1"), data.result("hz05a1"))
    fig.savefig("hz05a1.pdf")

The style follows the Arai-plot conventions of the paleointensity literature:
closed circles for the selected segment and open ones for the excluded steps,
triangles for pTRM checks joined to the step they check, squares for tail
checks, diamonds for additivity checks, the best-fit line across the selected
range, and the statistics that decided the interpretation in the corner.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Sequence

import numpy as np

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

import pmagpy.paleointensity as pint
from pmagpy import pint_stats as ps

SEGMENT = "#1f4e9c"
EXCLUDED = "#9aa3ad"
PTRM = "#2a9d8f"
TAIL = "#e76f51"
ADD = "#7b5ea7"
MEAN = "#e76f51"
EDGE = "#2b2b2b"
GREY = "#6b7280"

#: the statistics printed on a specimen figure, in the order analysts read them
HEADLINE = ("n", "B_anc", "beta", "FRAC", "f_vds", "g", "q", "k_prime", "MAD_Free", "DANG",
            "SCAT", "DRAT", "dTR", "Ziggie")


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_size(9)


def _headline(stats: Dict[str, ps.Stat], keys=HEADLINE) -> str:
    parts = []
    for key in keys:
        stat = stats.get(key)
        if stat is None:
            continue
        spec = ps.describe(key)
        parts.append(f"{spec.label} = {stat.text('{:.' + str(spec.decimals) + 'g}')}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Specimen
# ---------------------------------------------------------------------------
def arai_axes(ax, spec: pint.PintSpecimen, bounds, stats=None, normalize: bool = True,
              with_checks: bool = True, labels: bool = True) -> None:
    """Draw one specimen's Arai plot onto an existing axis."""
    arai = spec.arai
    scale = arai.y[0] if (normalize and arai.y[0]) else 1.0
    x, y = arai.x / scale, arai.y / scale
    lo, hi = bounds if bounds else (0, arai.n - 1)
    ax.plot(x, y, "-", color=EXCLUDED, lw=0.8, zorder=1)
    outside = [i for i in range(arai.n) if not (lo <= i <= hi)]
    ax.plot(x[outside], y[outside], "o", mfc="white", mec=EDGE, ms=5, lw=0, zorder=3)
    inside = list(range(lo, hi + 1))
    ax.plot(x[inside], y[inside], "o", mfc=SEGMENT, mec=EDGE, ms=6, lw=0, zorder=4)

    if stats and stats.get("b") and stats["b"].is_value:
        fit = ps.york_regression(x[inside], y[inside])
        span = np.array([float(np.min(x[inside])), float(np.max(x[inside]))])
        ax.plot(span, fit["y_int"] + fit["b"] * span, "-", color=SEGMENT, lw=1.6, zorder=5)

    if with_checks:
        for chk in arai.ptrm_checks:
            ax.plot([x[chk.i], chk.x / scale], [y[chk.i], y[chk.i]], "-", color=PTRM, lw=0.8,
                    zorder=2)
            ax.plot(chk.x / scale, y[chk.i], "^", color=PTRM, ms=6, zorder=5)
        for chk in arai.tail_checks:
            ax.plot([x[chk.i], x[chk.i]], [y[chk.i], chk.y / scale], "-", color=TAIL, lw=0.8,
                    zorder=2)
            ax.plot(x[chk.i], chk.y / scale, "s", mfc="white", mec=TAIL, mew=1.4, ms=6, zorder=5)
        for chk in arai.additivity_checks:
            ax.plot([x[chk.i], chk.x / scale], [y[chk.i], y[chk.i]], "-", color=ADD, lw=0.8,
                    zorder=2)
            ax.plot(chk.x / scale, y[chk.i], "D", color=ADD, ms=5, zorder=5)

    if labels:
        step = max(1, arai.n // 12)
        for i in range(0, arai.n, step):
            text = "NRM" if arai.steps[i] == "NRM" else f"{arai.temps[i] - pint.KELVIN_OFFSET:.0f}"
            ax.annotate(text, (x[i], y[i]), textcoords="offset points", xytext=(4, 4),
                        fontsize=6.5, color=GREY)
    ax.set_xlabel("pTRM gained" + ("  (NRM units)" if normalize else ""))
    ax.set_ylabel("NRM remaining" + ("  (NRM units)" if normalize else ""))
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    _style(ax)


def specimen_figure(spec: pint.PintSpecimen, bounds, stats: Optional[dict] = None,
                    result=None, with_checks: bool = True, figsize=(9.0, 5.4)):
    """An Arai plot with the Zijderveld diagram, the decay curve and the statistics."""
    fig = plt.figure(figsize=figsize)
    grid = fig.add_gridspec(2, 3, width_ratios=[2.1, 1.0, 1.0], height_ratios=[1, 1],
                            wspace=0.32, hspace=0.42)
    ax = fig.add_subplot(grid[:, 0])
    arai_axes(ax, spec, bounds, stats, with_checks=with_checks)

    zij_ax = fig.add_subplot(grid[0, 1])
    zij = pint.zijderveld_xy(spec)
    zij_ax.plot(zij["h_x"], zij["h_y"], "o-", color="#c8102e", ms=3.5, lw=0.8,
                label="horizontal")
    zij_ax.plot(zij["v_x"], zij["v_y"], "s-", color=SEGMENT, ms=3.5, lw=0.8, label="vertical")
    zij_ax.axhline(0, color=EDGE, lw=0.6)
    zij_ax.axvline(0, color=EDGE, lw=0.6)
    zij_ax.set_aspect("equal", adjustable="datalim")
    zij_ax.set_title("Zijderveld", fontsize=8)
    zij_ax.set_xticks([])
    zij_ax.set_yticks([])
    for side in ("top", "right", "bottom", "left"):
        zij_ax.spines[side].set_visible(False)

    decay_ax = fig.add_subplot(grid[1, 1])
    temps, decay = pint.decay_curve(spec)
    decay_ax.plot(temps - pint.KELVIN_OFFSET, decay, "o-", color=SEGMENT, ms=3.5, lw=0.9)
    if bounds:
        decay_ax.plot((temps[list(bounds)] - pint.KELVIN_OFFSET), decay[list(bounds)], "o",
                      mfc="none", mec=SEGMENT, mew=1.6, ms=8)
    decay_ax.set_xlabel("temperature (°C)")
    decay_ax.set_ylabel("M / NRM")
    _style(decay_ax)

    text_ax = fig.add_subplot(grid[:, 2])
    text_ax.axis("off")
    title = spec.name
    if result is not None and np.isfinite(result.b_anc):
        title += f"\n{result.b_anc:.1f} ± {result.sigma:.1f} µT"
        if result.corrected:
            title += f"\n(uncorrected {result.b_anc_uncorrected:.1f} µT)"
    text_ax.text(0, 1.0, title, va="top", ha="left", fontsize=10, fontweight="bold",
                 transform=text_ax.transAxes)
    text_ax.text(0, 0.86, f"{spec.arai.protocol} · B_lab {spec.blab_uT:.0f} µT",
                 va="top", ha="left", fontsize=8, color=GREY, transform=text_ax.transAxes)
    if stats:
        text_ax.text(0, 0.80, _headline(stats), va="top", ha="left", fontsize=8,
                     family="monospace", transform=text_ax.transAxes)
    if result is not None and result.corrections:
        applied = [f"{k} ×{c.factor:.3f}" for k, c in result.corrections.items() if c.applied]
        if applied:
            text_ax.text(0, 0.14, "corrections\n" + "\n".join(applied), va="top", ha="left",
                         fontsize=8, color=GREY, transform=text_ax.transAxes)
    handles = [Line2D([], [], marker="o", color="none", mfc=SEGMENT, mec=EDGE, label="selected"),
               Line2D([], [], marker="o", color="none", mfc="white", mec=EDGE, label="excluded"),
               Line2D([], [], marker="^", color="none", mfc=PTRM, mec=PTRM, label="pTRM check"),
               Line2D([], [], marker="s", color="none", mfc="white", mec=TAIL, label="tail check"),
               Line2D([], [], marker="D", color="none", mfc=ADD, mec=ADD, label="additivity")]
    text_ax.legend(handles=handles, loc="lower left", fontsize=7, frameon=False,
                   bbox_to_anchor=(0, -0.02))
    return fig


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
def site_figure(site: str, results: Sequence, accepted: Optional[set] = None,
                figsize=(7.5, 4.2)):
    """Every specimen of a site, with the mean of the accepted ones."""
    accepted = accepted or {r.specimen for r in results}
    fig, ax = plt.subplots(figsize=figsize)
    order = sorted(results, key=lambda r: r.b_anc if np.isfinite(r.b_anc) else np.inf)
    names = [r.specimen for r in order]
    values = [r.b_anc for r in order]
    errors = [r.sigma if np.isfinite(r.sigma) else 0.0 for r in order]
    colors = [SEGMENT if r.specimen in accepted else EXCLUDED for r in order]
    ax.errorbar(range(len(order)), values, yerr=errors, fmt="none", ecolor=EXCLUDED, lw=0.9)
    for i, (value, color) in enumerate(zip(values, colors)):
        ax.plot(i, value, "o", mfc=color, mec=EDGE, ms=7)
    good = [r.b_anc for r in order if r.specimen in accepted and np.isfinite(r.b_anc)]
    stats = ps.group_statistics(good)
    if stats["mean"]:
        mean, sd = float(stats["mean"]), float(stats["sd"]) if stats["sd"] else 0.0
        ax.axhline(mean, color=MEAN, lw=1.6)
        ax.axhspan(mean - sd, mean + sd, color=MEAN, alpha=0.12)
        ax.text(0.99, 0.97, f"{mean:.1f} ± {sd:.1f} µT   N = {len(good)}",
                transform=ax.transAxes, ha="right", va="top", fontsize=9, color=MEAN)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(names, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("paleointensity (µT)")
    ax.set_title(site, fontsize=10)
    _style(ax)
    fig.tight_layout()
    return fig


def study_figure(data: pint.PintData, level: str = "site", figsize=(8.0, 4.6)):
    """Every group mean in the study, in the order the groups are named."""
    frame = data.group_results(level=level)
    fig, ax = plt.subplots(figsize=figsize)
    if len(frame) == 0:
        ax.text(0.5, 0.5, "no accepted results", ha="center", va="center", fontsize=10,
                color=GREY, transform=ax.transAxes)
        ax.axis("off")
        return fig
    ax.errorbar(range(len(frame)), frame["int_abs"], yerr=frame["int_abs_sigma"].fillna(0),
                fmt="o", color=SEGMENT, ecolor=EXCLUDED, ms=6, mec=EDGE, lw=0.9)
    ax.set_xticks(range(len(frame)))
    ax.set_xticklabels(frame[level], rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("paleointensity (µT)")
    ax.set_title(f"{len(frame)} {level} means", fontsize=10)
    for i, row in enumerate(frame.itertuples()):
        ax.annotate(f"n={int(row.n)}", (i, row.int_abs), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=6.5, color=GREY)
    _style(ax)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# BiCEP
# ---------------------------------------------------------------------------
def bicep_figure(result, specimens: Optional[Sequence] = None, figsize=(8.4, 3.8)):
    """The BiCEP result: the bias line on the left, the posterior on the right."""
    fig, (left, right) = plt.subplots(1, 2, figsize=figsize,
                                      gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.32})
    names = list(result.specimen_k)
    k = np.array([result.specimen_k[n] for n in names])
    b = np.array([result.specimen_b.get(n, np.nan) for n in names])
    good = np.isfinite(k) & np.isfinite(b)
    left.plot(k[good], b[good], "o", mfc=SEGMENT, mec=EDGE, ms=7)
    for name, kx, by in zip(np.array(names)[good], k[good], b[good]):
        left.annotate(name, (kx, by), textcoords="offset points", xytext=(4, 4), fontsize=6.5,
                      color=GREY)
    if np.isfinite(result.b_site) and good.sum() >= 1:
        span = np.array([min(0.0, float(np.min(k[good]))), max(0.0, float(np.max(k[good])))])
        left.plot(span, result.b_site + result.slope * span, "-", color=MEAN, lw=1.6)
    if np.isfinite(result.b_site):
        left.plot(0, result.b_site, "*", color=MEAN, ms=15, mec=EDGE)
        left.errorbar(0, result.b_site,
                      yerr=[[result.b_site - result.ci_low], [result.ci_high - result.b_site]],
                      color=MEAN, capsize=4, lw=1.4)
    left.axvline(0, color=EDGE, lw=0.6, ls=":")
    left.set_xlabel("Arai plot curvature $k$")
    left.set_ylabel("specimen intensity (µT)")
    left.set_title(f"{result.site}: bias against curvature", fontsize=9)
    _style(left)

    if result.samples is not None and len(result.samples):
        right.hist(result.samples, bins=40, color=SEGMENT, alpha=0.8, edgecolor="none",
                   density=True)
        right.axvline(result.b_site, color=MEAN, lw=1.6)
        right.axvspan(result.ci_low, result.ci_high, color=MEAN, alpha=0.12)
        right.set_xlabel("site paleointensity (µT)")
        right.set_ylabel("posterior density")
        note = (f"{result.b_site:.1f} µT\n[{result.ci_low:.1f}, {result.ci_high:.1f}]\n"
                f"N = {len(result.specimens)}, {result.method}")
        if result.method != "bootstrap":
            note += f"\nR-hat {result.r_hat:.3f}, ESS {result.ess:.0f}"
        right.text(0.97, 0.95, note, transform=right.transAxes, ha="right", va="top",
                   fontsize=7.5, color=EDGE)
    else:
        right.text(0.5, 0.5, "no posterior draws", ha="center", va="center", color=GREY,
                   transform=right.transAxes)
        right.axis("off")
    _style(right)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------
def all_specimen_figures(data: pint.PintData, directory: str, fmt: str = "pdf",
                         specimens: Optional[Iterable[str]] = None,
                         progress=None) -> list:
    """Write one figure per interpreted specimen; returns the paths written."""
    import os
    os.makedirs(directory, exist_ok=True)
    names = list(specimens) if specimens is not None else list(data.interpretations)
    written = []
    for index, name in enumerate(names):
        result = data.result(name)
        if result is None:
            continue
        figure = specimen_figure(data.specimens[name], (result.imin, result.imax),
                                 data.statistics(name), result)
        path = os.path.join(directory, f"{name}.{fmt}")
        figure.savefig(path, format=fmt, bbox_inches="tight")
        plt.close(figure)
        written.append(path)
        if progress is not None:
            progress((index + 1) / len(names), name)
    return written

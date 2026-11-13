"""
The Inspect page: look at the data of a study, or of a conversion before it is written.

One specimen at a time, in specimen, geographic or tilt-corrected coordinates:
its demagnetization steps as PmagPy draws them -- the Zijderveld diagram with
the fits the specimens table holds (``pmagplotlib.plot_zij``), the equal-area
projection (``ipmag.plot_net``, ``ipmag.plot_di``) and the demagnetization
curve (``pmagplotlib.plot_mag``) -- the steps themselves (``pmag.find_dmag_rec``,
rotated with ``pmag.dogeo`` and ``pmag.dotilt`` and the sample's orientation),
the fits, and where the specimen sits: its sample's orientation and bedding,
its site's position, age and lithology.

The Convert page's "Preview" converts the chosen files into a scratch folder and
opens this page on it, so that what a conversion makes can be looked at before
anything is written into the study.

The data functions (:func:`read_tables`, :func:`steps`, :func:`fits`,
:func:`context`, :func:`figure`) take the tables and return plain values, so a
notebook can use them as well.
"""
from __future__ import annotations

import html
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import panel as pn
from matplotlib.figure import Figure

from pmagpy import ipmag, pmag, pmagplotlib
from pmagpy_panel.theme import MUTED_STYLE
from pmagpy_panel.widgets import LayoutHold
from .home import CSS, shorten_home

TABLES = ("measurements", "specimens", "samples", "sites", "locations")
COORDS = {"specimen": -1, "geographic": 0, "tilt-corrected": 100}
FIT_COLORS = ("#2a9d8f", "#e76f51", "#6a4c93", "#f4a261", "#264653")


# ----- the data -----------------------------------------------------------------------------------
def read_tables(directory: str) -> Dict[str, pd.DataFrame]:
    """The MagIC tables of a directory, as text (empty cells ""); a table that is not there is left out."""
    tables = {}
    for table in TABLES:
        path = os.path.join(directory, table + ".txt")
        if os.path.isfile(path):
            tables[table] = pd.read_csv(path, sep="\t", header=1, dtype=str, keep_default_na=False, quoting=3)
    return tables


def _number(value) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(number) else number


def specimen_names(tables: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    """The specimens with measurements, by site (``""`` for those without one), in the order of the table."""
    meas = tables.get("measurements")
    if meas is None or "specimen" not in meas:
        return {}
    names = list(dict.fromkeys(meas["specimen"]))
    site_of = {}
    samples, specimens = tables.get("samples"), tables.get("specimens")
    sample_site = dict(zip(samples["sample"], samples["site"])) if samples is not None and \
        {"sample", "site"} <= set(samples) else {}
    if specimens is not None and {"specimen", "sample"} <= set(specimens):
        site_of = {s: sample_site.get(p, "") for s, p in zip(specimens["specimen"], specimens["sample"])}
    groups: Dict[str, List[str]] = {}
    for name in names:
        groups.setdefault(site_of.get(name, ""), []).append(name)
    return groups


def orientation(tables: Dict[str, pd.DataFrame], specimen: str) -> Dict[str, Optional[float]]:
    """The azimuth, dip, bed_dip_direction and bed_dip of a specimen's sample (None when not given)."""
    out = {k: None for k in ("azimuth", "dip", "bed_dip_direction", "bed_dip")}
    sample = context(tables, specimen).get("sample")
    samples = tables.get("samples")
    if not sample or samples is None:
        return out
    rows = samples[samples["sample"] == sample]
    for _, row in rows.iterrows():
        for k in out:
            if out[k] is None and k in row:
                out[k] = _number(row[k])
    return out


def available_coords(tables: Dict[str, pd.DataFrame], specimen: str) -> List[str]:
    """The coordinate systems a specimen can be shown in: geographic with an orientation, tilt-corrected with
    bedding as well."""
    o = orientation(tables, specimen)
    out = ["specimen"]
    if o["azimuth"] is not None and o["dip"] is not None:
        out.append("geographic")
        if o["bed_dip_direction"] is not None and o["bed_dip"] is not None:
            out.append("tilt-corrected")
    return out


def _rotate(dec: float, inc: float, o: Dict[str, Optional[float]], coord: str) -> Tuple[float, float]:
    if coord == "specimen":
        return dec, inc
    dec, inc = pmag.dogeo(dec, inc, o["azimuth"], o["dip"])
    if coord == "tilt-corrected":
        dec, inc = pmag.dotilt(dec, inc, o["bed_dip_direction"], o["bed_dip"])
    return dec, inc


def steps(tables: Dict[str, pd.DataFrame], specimen: str, coord: str = "specimen") -> Tuple[list, str]:
    """A specimen's demagnetization steps as ``pmag.find_dmag_rec`` gives them -- [treatment, dec, inc,
    intensity, ZI, quality, instrument] -- in the coordinate system asked for, and their units (T, K ...)."""
    meas = tables.get("measurements")
    if meas is None:
        return [], ""
    block, units = pmag.find_dmag_rec(specimen, meas[meas["specimen"] == specimen], version=3)
    if coord != "specimen":
        o = orientation(tables, specimen)
        block = [[rec[0], *_rotate(rec[1], rec[2], o, coord), *rec[3:]] for rec in block]
    return block, units


def fits(tables: Dict[str, pd.DataFrame], specimen: str, coord: str = "specimen") -> pd.DataFrame:
    """The fits the specimens table holds for a specimen in a coordinate system: component, fit type, direction,
    MAD, number of steps and step range."""
    columns = ["component", "type", "dec", "inc", "mad", "n", "min", "max", "unit"]
    specimens = tables.get("specimens")
    if specimens is None or "dir_dec" not in specimens:
        return pd.DataFrame(columns=columns)
    rows = specimens[(specimens["specimen"] == specimen) & (specimens["dir_dec"] != "")]
    out = []
    for _, row in rows.iterrows():
        tilt = _number(row.get("dir_tilt_correction"))
        if tilt is None or int(tilt) != COORDS[coord]:
            continue
        codes = str(row.get("method_codes", "")).split(":")
        kind = next((c for c in ("DE-BFL-A", "DE-BFL-O", "DE-BFL", "DE-BFP", "DE-FM", "DE-VM") if c in codes), "")
        if not kind:
            continue
        out.append({"component": row.get("dir_comp", ""), "type": kind, "dec": _number(row["dir_dec"]),
                    "inc": _number(row.get("dir_inc")),
                    "mad": _number(row.get("dir_mad_free")) or _number(row.get("dir_mad_anc")),
                    "n": row.get("dir_n_measurements", ""), "min": _number(row.get("meas_step_min")),
                    "max": _number(row.get("meas_step_max")), "unit": row.get("meas_step_unit", "")})
    return pd.DataFrame(out, columns=columns)


def context(tables: Dict[str, pd.DataFrame], specimen: str) -> Dict[str, str]:
    """Where a specimen sits: its sample, site and location, and the site's position, age and lithology."""
    out = {"specimen": specimen}
    specimens = tables.get("specimens")
    if specimens is not None and {"specimen", "sample"} <= set(specimens):
        rows = specimens[(specimens["specimen"] == specimen) & (specimens["sample"] != "")]
        if len(rows):
            out["sample"] = rows.iloc[0]["sample"]
    samples, sites = tables.get("samples"), tables.get("sites")
    if out.get("sample") and samples is not None and "site" in samples:
        rows = samples[(samples["sample"] == out["sample"]) & (samples["site"] != "")]
        if len(rows):
            out["site"] = rows.iloc[0]["site"]
    if out.get("site") and sites is not None:
        rows = sites[sites["site"] == out["site"]]
        for col in ("location", "lat", "lon", "age", "age_low", "age_high", "age_unit", "lithologies",
                    "geologic_classes"):
            values = [v for v in rows.get(col, pd.Series(dtype=str)) if v]
            if values:
                out[col] = values[0]
    return out


def _step_value(treatment: float, units: str) -> float:
    """A treatment in the units an analyst reads: mT for a field, degrees C for a temperature."""
    if treatment < 1:          # tesla
        return round(treatment * 1e3, 3)
    return round(treatment - 273, 1)


def figure(tables: Dict[str, pd.DataFrame], specimen: str, coord: str = "specimen") -> Optional[Figure]:
    """The Zijderveld diagram with the stored line fits, the equal-area projection of the steps and fits, and
    the demagnetization curve of a specimen, drawn by PmagPy's own plotting functions."""
    block, units = steps(tables, specimen, coord)
    if len(block) < 2:
        return None
    fig = Figure(figsize=(13, 4.3))
    zij, net, mag = fig.add_subplot(1, 3, 1), fig.add_subplot(1, 3, 2), fig.add_subplot(1, 3, 3)
    stored = fits(tables, specimen, coord)
    arrows = []
    for k, f in enumerate(stored.itertuples()):
        if f.type == "DE-BFP" or f.dec is None or f.min is None:
            continue
        arrows.append({"specimen_dec": f.dec, "specimen_inc": f.inc, "measurement_step_min": f.min,
                       "measurement_step_max": f.max, "calculation_type": f.type,
                       "color": FIT_COLORS[k % len(FIT_COLORS)], "label": f.component})
    good = [rec for rec in block if rec[5] == "g"]
    labels = [f"{_step_value(rec[0], units):g}" if i in (0, len(good) - 1) else "" for i, rec in enumerate(good)]
    pmagplotlib.plot_zij(None, block, 0., f"{specimen} ({coord})", norm=False, ax=zij, frame=False,
                         axis_labels={"right": "N" if coord != "specimen" else "X",
                                      "bottom": "E, Down" if coord != "specimen" else "Y, Z"},
                         step_labels=labels, fits=arrows or None)
    if arrows:
        zij.legend(fontsize=8, loc="best", frameon=False)
    ipmag.plot_net(ax=net)
    decs, incs = [rec[1] for rec in good], [rec[2] for rec in good]
    if decs:
        ipmag.plot_di(dec=decs, inc=incs, ax=net, color="#c0392b", markersize=18, connect_points=True, lc="#c0392b")
    bad = [rec for rec in block if rec[5] != "g"]
    if bad:
        ipmag.plot_di(dec=[r[1] for r in bad], inc=[r[2] for r in bad], ax=net, color="#9ca3af", marker="x",
                      markersize=24)
    for k, f in enumerate(stored.itertuples()):
        if f.dec is not None and f.inc is not None:
            ipmag.plot_di(dec=[f.dec], inc=[f.inc], ax=net, color=FIT_COLORS[k % len(FIT_COLORS)],
                          marker="s" if f.type == "DE-BFP" else "*", markersize=90, edge="k")
    net.set_title("equal area (" + ("x: excluded, " if bad else "") + "★ fit, ■ pole of plane)", fontsize=9)
    unit = "T" if "T" in units and "K" not in units else ("K" if "K" in units and "T" not in units else units)
    pmagplotlib.plot_mag(None, block, "demagnetization", 0, unit, 1, ax=mag)
    fig.tight_layout()
    return fig


def steps_table(tables: Dict[str, pd.DataFrame], specimen: str, coord: str = "specimen") -> pd.DataFrame:
    """The steps as a table to read: treatment (mT or °C), dec and inc in the coordinate system, intensity,
    quality and method codes."""
    block, units = steps(tables, specimen, coord)
    meas = tables["measurements"]
    rows = meas[meas["specimen"] == specimen]
    codes = [c for c in rows.get("method_codes", pd.Series([""] * len(rows)))]
    unit_label = "mT" if "T" in units and "K" not in units else ("°C" if "K" in units and "T" not in units else "")
    out = pd.DataFrame({f"step {unit_label}".strip(): [_step_value(r[0], units) for r in block],
                        "dec": [round(r[1], 1) if r[1] != "" else None for r in block],
                        "inc": [round(r[2], 1) if r[2] != "" else None for r in block],
                        "intensity": [r[3] for r in block], "quality": [r[5] for r in block]})
    if len(codes) == len(out):
        out["method codes"] = codes
    return out


# ----- the page -----------------------------------------------------------------------------------
class InspectorView:
    """The Inspect page, on the session's directory or on a preview folder."""

    def __init__(self, session):
        self.s = session
        self.directory = ""
        self.preview = False
        self.tables: Dict[str, pd.DataFrame] = {}
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.banner = pn.pane.HTML("", sizing_mode="stretch_width", visible=False)
        self.home_btn = pn.widgets.Button(name="← Home", button_type="default", width=110, margin=(30, 0, 0, 0))
        self.specimen = pn.widgets.Select(name="Specimen", width=260)
        self.prev_btn = pn.widgets.Button(name="◀", width=40, margin=(28, 2, 0, 10))
        self.next_btn = pn.widgets.Button(name="▶", width=40, margin=(28, 10, 0, 2))
        self.coord = pn.widgets.RadioButtonGroup(options=list(COORDS), value="specimen", button_type="light",
                                                 margin=(28, 10, 0, 10))
        self.context_pane = pn.pane.HTML("", sizing_mode="stretch_width")
        self.plot = pn.pane.Matplotlib(None, dpi=96, tight=True, sizing_mode="stretch_width", height=430)
        self.steps_pane = pn.widgets.Tabulator(pd.DataFrame(), disabled=True, show_index=False, height=300,
                                               sizing_mode="stretch_width", layout="fit_data_table")
        self.fits_pane = pn.widgets.Tabulator(pd.DataFrame(), disabled=True, show_index=False, height=140,
                                              sizing_mode="stretch_width", layout="fit_data_table")
        self.specimen.param.watch(lambda e: self._draw(), "value")
        self.coord.param.watch(lambda e: self._draw(), "value")
        self.prev_btn.on_click(lambda e: self._step(-1))
        self.next_btn.on_click(lambda e: self._step(1))
        session.param.watch(lambda e: self.refresh(), "directory")

    # ----- what is shown ----------------------------------------------------------------------------
    def show_directory(self, directory: str, preview: bool = False, note: str = "") -> None:
        """Look at the tables of ``directory``: the study's own, or a preview a conversion wrote elsewhere."""
        self.directory, self.preview = directory, preview
        self.tables = read_tables(directory) if directory else {}
        groups = specimen_names(self.tables)
        options = {site or "(no site)": names for site, names in groups.items()}
        with LayoutHold.batch():
            self.specimen.groups = options if options else {"(no specimens)": [""]}
            first = next((names[0] for names in groups.values() if names), "")
            self.specimen.value = first
            title = "Preview" if preview else "Inspect"
            self.heading.object = (f'<div class="home"><div class="section">{title}</div>'
                                   f'<h1>{html.escape(os.path.basename(directory.rstrip(os.sep)) or "—")}</h1>'
                                   f'<div class="path">{html.escape(shorten_home(directory))}</div></div>')
            self.banner.visible = preview
            self.home_btn.name = "← Convert" if preview else "← Home"
            self.banner.object = (f'<div style="background:#fff7db;border:1px solid #f0d78c;border-radius:6px;'
                                  f'padding:8px 12px">What the conversion would write: nothing is in the study yet. '
                                  f'{html.escape(note)}</div>')
            self._draw()

    def refresh(self) -> None:
        if not self.preview:
            self.show_directory(self.s.directory or "")

    def reset(self) -> None:
        """Back on the page from Home: the study's own tables, as they are now."""
        if not self.preview:
            self.show_directory(self.s.directory or "")

    def _names(self) -> List[str]:
        return [n for names in specimen_names(self.tables).values() for n in names]

    def _step(self, by: int) -> None:
        names = self._names()
        if self.specimen.value in names:
            self.specimen.value = names[(names.index(self.specimen.value) + by) % len(names)]

    def _draw(self) -> None:
        name = self.specimen.value
        if not name or "measurements" not in self.tables:
            self.context_pane.object = f'<div style="{MUTED_STYLE}">No measurements here.</div>'
            self.plot.object = None
            return
        coords = available_coords(self.tables, name)
        coord = self.coord.value if self.coord.value in coords else "specimen"
        info = context(self.tables, name)
        o = orientation(self.tables, name)
        parts = [f"<b>{html.escape(k)}</b> {html.escape(str(info[k]))}" for k in ("sample", "site", "location")
                 if info.get(k)]
        if info.get("lat") and info.get("lon"):
            parts.append(f"{html.escape(info['lat'])}° N, {html.escape(info['lon'])}° E")
        if info.get("age") or info.get("age_low"):
            parts.append("age " + html.escape(info.get("age") or f"{info.get('age_low')}–{info.get('age_high')}")
                         + " " + html.escape(info.get("age_unit", "")))
        if info.get("lithologies"):
            parts.append(html.escape(info["lithologies"]))
        if o["azimuth"] is not None:
            parts.append(f"azimuth {o['azimuth']:g}, dip {o['dip']:g}")
        if o["bed_dip"] is not None:
            parts.append(f"bedding {o['bed_dip_direction']:g}/{o['bed_dip']:g}")
        missing = [c for c in COORDS if c not in coords]
        note = (f' <span style="{MUTED_STYLE}">· no {" or ".join(missing)} coordinates: '
                f'{"no orientation" if "geographic" in missing else "no bedding"}</span>') if missing else ""
        with LayoutHold.batch():
            self.context_pane.object = '<div style="font-size:.92rem">' + " · ".join(parts) + note + "</div>"
            self.plot.object = figure(self.tables, name, coord)
            self.steps_pane.value = steps_table(self.tables, name, coord)
            shown = fits(self.tables, name, coord)
            for col in ("min", "max"):           # in mT or degrees C, as the steps are listed
                shown[col] = [_step_value(v, u) if v is not None else None for v, u in zip(shown[col], shown["unit"])]
            unit = {"T": "mT", "K": "°C"}.get(next(iter(shown["unit"]), ""), "")
            self.fits_pane.value = shown.drop(columns=["unit"]).rename(
                columns={"min": f"from {unit}".strip(), "max": f"to {unit}".strip()})

    def panel(self) -> pn.Column:
        return pn.Column(
            pn.Row(self.heading, self.home_btn, sizing_mode="stretch_width"),
            self.banner,
            pn.Row(self.specimen, self.prev_btn, self.next_btn, self.coord, sizing_mode="stretch_width"),
            self.context_pane, self.plot,
            pn.pane.HTML('<div class="section" style="margin-top:6px">Fits in the specimens table</div>',
                         stylesheets=[CSS]),
            self.fits_pane,
            pn.pane.HTML('<div class="section" style="margin-top:6px">Steps</div>', stylesheets=[CSS]),
            self.steps_pane,
            sizing_mode="stretch_width", max_width=1300, margin=(18, 40, 40, 40),
        )

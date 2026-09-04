"""
The panes: the dataset block, the selection (which specimens, which frame),
the inventory, and one view per question — where do the eigenvectors point
and how well are they known (Eigenvectors), what shape is the fabric (Shape),
the tensors themselves (Specimens), and the tensors from the measurements
that have not been reduced yet (Reduce).

Each view is a Panel layout over ``pmagpy.anisotropy``: the widgets are the
arguments of ``group_statistics``, and the view's "show code" block is the
call it is making. A view is built from a :class:`Session`, or — in a
notebook — straight from a specimens DataFrame::

    EigenvectorsView(specimens).panel()
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import panel as pn

from pmagpy import anisotropy
from pmagpy_panel import code
from pmagpy_panel.chooser import DirectoryChooser
from pmagpy_panel.results import TableSave
from pmagpy_panel.theme import MUTED_STYLE, SECTION_STYLE, kpi
from . import plots
from .session import ALL, APP, LEVELS, RECENT_FILE, Session, as_session, env

MEAN_TABLES = {"site": "sites", "sample": "samples"}      # where a group mean is written

WATCHED = ["version", "coordinates", "level", "group", "aniso_type"]   # session parameters every view follows
                                                                        # (version: the tables changed — load, reload)


def section(title: str) -> pn.pane.HTML:
    return pn.pane.HTML(f'<div style="{SECTION_STYLE}">{title}</div>', margin=(10, 0, 0, 0))


def muted(text: str) -> str:
    return f'<div style="{MUTED_STYLE}">{text}</div>'


def preamble(session: Session) -> list:
    """The lines that get the tensors into a notebook: the tables, then ``tensor_table`` in the session's frame."""
    lines = ["import pandas as pd", "import pmagpy.anisotropy as aniso", "import pmagpy.contribution_builder as cb", ""]
    if session.directory:
        lines += [code.assign("contribution", code.call("cb.Contribution", session.directory)),
                  "specimens = contribution.tables['specimens'].df",
                  "samples = contribution.tables['samples'].df if 'samples' in contribution.tables else None"]
    else:
        lines += ["# specimens, samples: the DataFrames this view was given"]
    lines.append(code.assign("tensors", code.call("aniso.tensor_table", code.Name("specimens"), code.Name("samples"),
                                                  coordinates=session.coordinates)))
    return lines


def selection_lines(session: Session) -> list:
    """The filter that picks the session's group (and type) out of ``tensors``."""
    lines = []
    if session.group != ALL:
        lines.append(f"tensors = tensors[tensors[{session.level!r}] == {session.group!r}]")
    if session.aniso_type:
        lines.append(f"tensors = tensors[tensors['aniso_type'] == {session.aniso_type!r}]")
    return lines


def _fmt(value, digits: int = 4) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "—" if not np.isfinite(v) else f"{v:.{digits}f}"


def _table(head: list, rows: list) -> str:
    th = "".join(f'<th style="text-align:{"left" if i == 0 else "right"};font-weight:normal;padding:0 0 0 18px">{h}</th>'
                 for i, h in enumerate(head))
    body = "".join("<tr>" + "".join(f'<td style="text-align:{"left" if i == 0 else "right"};padding:1px 0 1px 18px">'
                                    f'{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return (f'<table style="border-collapse:collapse;font-size:0.9rem"><tr style="{MUTED_STYLE}">{th}</tr>'
            f'{body}</table>')


# ----------------------------------------------------------------------------- dataset, selection, inventory
class DataView(DirectoryChooser):
    """Switch between MagIC directories (the toolkit's chooser, counting tensors)."""

    def __init__(self, session: Session, chooser=None, chooser_available=None):
        super().__init__(
            session, recent_file=RECENT_FILE, chooser=chooser, chooser_available=chooser_available,
            chooser_stub=env("CHOOSER_STUB"), require_measurements=False,
            count=lambda s: f"{s.n_specimens()} specimens with tensors · {len(s.groups('site')) - 1} sites",
            note="A MagIC directory whose specimens.txt carries anisotropy tensors (aniso_s) — from a Kappabridge "
                 "converter, from aarm_magic/atrm_magic or from the Reduce tab here, which fits them to the "
                 "AARM/ATRM steps in measurements.txt. Sample orientations in samples.txt let specimen "
                 "tensors be rotated to geographic and tilt-corrected coordinates here.")


class SelectionView:
    """The side column's pickers: level and group, coordinate frame, anisotropy type — all held by the session."""

    def __init__(self, session: Session):
        self.s = session
        self.level = pn.widgets.Select(name="Group by", options=list(LEVELS), value=session.level, width=130)
        self.group = pn.widgets.Select(name="Group", options=[ALL], value=ALL, width=200)
        self.coordinates = pn.widgets.RadioButtonGroup(name="Coordinates", options=[], button_type="default",
                                                       button_style="outline", sizing_mode="stretch_width")
        self.aniso_type = pn.widgets.Select(name="Anisotropy type", options=[""], value="", width=130, visible=False)
        self.note = pn.pane.HTML("", sizing_mode="stretch_width")
        self._quiet = False
        self.level.param.watch(self._on_level, "value")
        self.group.param.watch(self._on_group, "value")
        self.coordinates.param.watch(self._on_coordinates, "value")
        self.aniso_type.param.watch(self._on_type, "value")
        session.param.watch(lambda e: self.reset(), "version")
        session.param.watch(lambda e: self.follow(), ["coordinates", "level", "group", "aniso_type"])
        self.reset()

    # ----- widgets -> session ---------------------------------------------------
    def _on_level(self, event) -> None:
        if self._quiet:
            return
        self.s.level = event.new
        self._quiet = True
        self.group.options = self.s.groups(event.new)
        self.group.value = ALL
        self._quiet = False
        self.s.group = ALL

    def _on_group(self, event) -> None:
        if not self._quiet:
            self.s.group = event.new

    def _on_coordinates(self, event) -> None:
        if not self._quiet and event.new:
            self.s.coordinates = self._frame_keys[self.coordinates.options.index(event.new)]

    def _on_type(self, event) -> None:
        if not self._quiet:
            self.s.aniso_type = event.new

    # ----- session -> widgets ---------------------------------------------------
    def reset(self) -> None:
        """New data: offer the groups, the frames that have tensors, the types when there are several."""
        counts = self.s.frame_counts()
        frames = self.s.frames()
        self._frame_keys = [k for k in anisotropy.COORDINATES if counts[k]]
        labels = []
        for k in self._frame_keys:
            rotated = counts[k] - frames[k]
            labels.append(f"{anisotropy.COORDINATE_NAMES[k]} ({counts[k]})"
                          + (f"*" if rotated else ""))
        self._quiet = True
        self.coordinates.options = labels
        self.level.options = list(LEVELS)
        self.aniso_type.options = [""] + self.s.types()
        self.aniso_type.visible = len(self.s.types()) > 1
        self._quiet = False
        self.follow()
        rotated_any = any(counts[k] > frames[k] for k in self._frame_keys)
        self.note.object = muted("* includes tensors rotated here from specimen coordinates with the sample "
                                 "orientations") if rotated_any else ""

    def follow(self) -> None:
        """Show the session's selection in the widgets without echoing it back."""
        self._quiet = True
        self.level.value = self.s.level
        self.group.options = self.s.groups()
        self.group.value = self.s.group if self.s.group in self.group.options else ALL
        if self.s.coordinates in self._frame_keys:
            self.coordinates.value = self.coordinates.options[self._frame_keys.index(self.s.coordinates)]
        self.aniso_type.value = self.s.aniso_type if self.s.aniso_type in self.aniso_type.options else ""
        self._quiet = False

    def panel(self) -> pn.Column:
        return pn.Column(section("Selection"), pn.Row(self.level, self.group), self.aniso_type,
                         pn.pane.HTML(muted("Coordinates"), margin=(6, 0, 0, 10)), self.coordinates, self.note,
                         sizing_mode="stretch_width")


class Inventory:
    """The side column's inventory: specimens with tensors by type, and how many are in (or can reach) each frame."""

    def __init__(self, session: Session):
        self.s = session
        self.html = pn.pane.HTML("", sizing_mode="stretch_width")
        session.param.watch(lambda e: self.refresh(), "version")
        self.refresh()

    def refresh(self) -> None:
        index = self.s.index()
        if not len(index):
            self.html.object = muted("no anisotropy tensors in specimens.txt")
            return
        rows = []
        for t, sub in index.groupby(index["aniso_type"].fillna("untyped").astype(str), sort=False):
            frames = "".join(f'<td style="text-align:right;{MUTED_STYLE}">'
                             f'{int(sub["frames"].str.contains(k).sum())}</td>' for k in anisotropy.COORDINATES)
            rows.append(f'<tr><td>{t}</td><td style="text-align:right"><b>{len(sub)}</b></td>{frames}</tr>')
        head = (f'<tr style="{MUTED_STYLE}"><th style="text-align:left;font-weight:normal">type</th>'
                f'<th style="text-align:right;font-weight:normal">specimens</th>'
                f'<th style="text-align:right;font-weight:normal">s</th>'
                f'<th style="text-align:right;font-weight:normal">g</th>'
                f'<th style="text-align:right;font-weight:normal">t</th></tr>')
        counts = self.s.frame_counts()
        frames = self.s.frames()
        rotatable = counts["g"] - frames["g"]
        tilt = counts["t"] - frames["t"]
        notes = []
        if rotatable:
            notes.append(f"{rotatable} rotatable to geographic")
        if tilt:
            notes.append(f"{tilt} to tilt-corrected")
        note = muted(" · ".join(notes) + " with sample orientations") if notes else ""
        self.html.object = f'<table style="width:100%;border-collapse:collapse">{head}{"".join(rows)}</table>{note}'

    def panel(self) -> pn.Column:
        return pn.Column(section("Tensors"), self.html, sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- eigenvectors
class EigenvectorsView:
    """Eigenvectors on equal-area nets and the statistics of the selection's mean tensor.

    The specimens' V1/V2/V3 on one net; the mean tensor's eigenvectors with
    their Hext (1963) ellipses and, when asked, the bootstrap ellipses of
    ``pmag.sbootpars`` on the other. The options are ``group_statistics``'s
    arguments; a single specimen gets the Hext statistics of its own
    measurement scatter. A site's or sample's mean can be saved to its row
    of ``sites.txt``/``samples.txt`` (``anisotropy.mean_record``,
    ``add_mean_to_table``) through the toolkit's :class:`TableSave`.
    """

    TYPE = "eigenvectors"

    def __init__(self, session):
        self.s = as_session(session)
        self.hext = pn.widgets.Checkbox(name="Hext statistics", value=True)
        self.bootstrap = pn.widgets.Checkbox(name="bootstrap", value=False)
        self.parametric = pn.widgets.Checkbox(name="parametric", value=False)
        self.n_bootstraps = pn.widgets.IntSlider(name="bootstraps", start=100, end=5000, step=100, value=1000,
                                                 width=200)
        self.seed = pn.widgets.IntInput(name="seed", value=0, start=0, width=90)
        self.cloud = pn.widgets.Checkbox(name="bootstrap eigenvectors", value=False)
        self.compare = pn.widgets.Checkbox(name="comparison direction", value=False)
        self.compare_dec = pn.widgets.FloatInput(name="dec", value=0.0, start=0, end=360, step=1, width=80)
        self.compare_inc = pn.widgets.FloatInput(name="inc", value=90.0, start=-90, end=90, step=1, width=80)
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.specimen_net = pn.pane.Bokeh()
        self.mean_net = pn.pane.Bokeh()
        self.cdf = pn.pane.Bokeh()
        self.cdf_box = pn.Column(self.cdf, visible=False)      # toggled instead of the pane: Panel's Bokeh pane
                                                                # trips over its stylesheets when its visibility changes
        self.table = pn.pane.HTML("", sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.save = TableSave(self.s, self.code, "mean tensor", table="sites", app=APP,
                              label=lambda: self.s.selection_label())
        self.stats: Optional[dict] = None
        self.tensors = pd.DataFrame()

        for w in (self.hext, self.bootstrap, self.parametric, self.cloud, self.compare, self.compare_dec,
                  self.compare_inc, self.seed):
            w.param.watch(lambda e: self.refresh(), "value")
        self.n_bootstraps.param.watch(lambda e: self.refresh(), "value_throttled")
        self.s.param.watch(lambda e: self.refresh(), WATCHED)
        self.refresh()

    def set_parameters(self, **values) -> None:
        """Set several widgets and refresh once (tests, notebooks)."""
        for name, value in values.items():
            getattr(self, name).value = value
        self.refresh()

    # ----- the statistics ---------------------------------------------------------
    def statistics(self, tensors: pd.DataFrame) -> Optional[dict]:
        """``group_statistics`` of the selection; one specimen's own Hext statistics when it is alone."""
        if len(tensors) >= 2:
            return anisotropy.group_statistics(list(tensors["s"]), hext=self.hext.value, bootstrap=self.bootstrap.value,
                                               parametric=self.parametric.value, n_bootstraps=self.n_bootstraps.value,
                                               random_seed=self.seed.value)
        if len(tensors) == 1:
            row = tensors.iloc[0]
            stats = {"n": 1, "s": np.asarray(row["s"], float), "hext": None, "bootstrap": None}
            stats.update(anisotropy.eigenparameters(row["s"]))
            sigma, n = row.get("aniso_s_sigma"), row.get("aniso_s_n_measurements")
            aniso_type = str(row.get("aniso_type") or "")
            if self.hext.value and pd.notna(sigma) and pd.notna(n) and float(sigma) > 0 \
                    and anisotropy.degrees_of_freedom(int(n), aniso_type) > 0:
                stats["hext"] = anisotropy.specimen_hext(row["s"], float(sigma), int(n), aniso_type)
                stats["specimen_hext"] = True
            return stats
        return None

    def refresh(self) -> None:
        self.tensors = t = self.s.selection()
        self.stats = stats = self.statistics(t)
        comparison = (self.compare_dec.value, self.compare_inc.value) if self.compare.value else None
        self.specimen_net.object = plots.specimen_net(t)
        self.mean_net.object = plots.mean_net(stats, show_hext=self.hext.value, show_bootstrap=self.bootstrap.value,
                                              cloud=self.cloud.value, comparison=comparison)
        boot = stats.get("bootstrap") if stats else None
        if boot is not None:
            self.cdf.object = plots.eigenvalue_cdf(boot["taus"], anisotropy.bootstrap_eigenvalue_bounds(boot["taus"]))
        self.cdf_box.visible = boot is not None
        self.parametric.visible = self.n_bootstraps.visible = self.seed.visible = self.cloud.visible = \
            self.bootstrap.value
        self.compare_dec.visible = self.compare_inc.visible = self.compare.value
        self._summarize(stats)
        self._emit(stats)
        self._offer(stats)

    # ----- the save ---------------------------------------------------------------
    def mean_type(self) -> Optional[str]:
        """The one anisotropy type in the selection, or None when it mixes several."""
        if self.s.aniso_type:
            return self.s.aniso_type
        types = [str(t) for t in self.tensors["aniso_type"].dropna().unique()] if len(self.tensors) else []
        return types[0] if len(types) == 1 else None

    def _offer(self, stats: Optional[dict]) -> None:
        """A site's or sample's mean of two or more tensors can go to its row; say why anything else cannot."""
        s = self.s
        if s.level not in MEAN_TABLES:
            self.save.decline("a mean is saved for a site or a sample — group by one of those to write it")
            return
        self.save.set_table(MEAN_TABLES[s.level])
        if s.group == ALL:
            self.save.decline(f"pick one {s.level} to save its mean tensor to its row of {self.save.table}.txt")
            return
        if stats is None or stats["n"] < 2:
            self.save.decline("a mean needs at least two tensors")
            return
        aniso_type = self.mean_type()
        if aniso_type is None:
            self.save.decline("the selection mixes anisotropy types — pick one to save its mean")
            return
        record = anisotropy.mean_record(stats, aniso_type, s.coordinates, specimens=list(self.tensors["specimen"]))
        parent_column = {"site": "location", "sample": "site"}[s.level]
        parents = self.tensors[parent_column].dropna().astype(str).unique() if parent_column in self.tensors else []
        parent = {parent_column: str(parents[0])} if len(parents) == 1 else None
        level, group, table = s.level, s.group, self.save.table
        lines = [code.assign("record", code.call("aniso.mean_record", code.Name("stats"), aniso_type, s.coordinates,
                                                 specimens=code.Name("list(tensors['specimen'])"))),
                 code.assign(table, code.call("aniso.add_mean_to_table", code.Name(table), level, group,
                                              code.Name("record"), parent=parent))]
        self.save.offer(lambda df: anisotropy.add_mean_to_table(df, level, group, record, parent=parent),
                        lines, self.code.text.splitlines())

    def _summarize(self, stats: Optional[dict]) -> None:
        label = self.s.selection_label()
        if stats is None:
            self.summary.object = kpi([label, ("specimens", 0)]) + muted("nothing selected in this frame")
            self.table.object = ""
            return
        items = [label, ("specimens", stats["n"]), ("P′", _fmt(stats["aniso_pp"], 3)), ("T", _fmt(stats["aniso_t"], 3))]
        h = stats.get("hext")
        if h is not None:
            items.append(("F", f"{_fmt(h['F'], 2)} (crit {h['F_crit']})"))
        self.summary.object = kpi(items)
        head = ["axis", "τ", "dec", "inc"]
        if h is not None:
            head += ["Hext ellipse semi-axes"]
        boot = stats.get("bootstrap")
        if boot is not None:
            head += ["bootstrap ζ / η", "τ 95% bounds"]
            bounds = anisotropy.bootstrap_eigenvalue_bounds(boot["taus"])
        rows = []
        pairs = {"v1": ("e12", "e13"), "v2": ("e23", "e12"), "v3": ("e13", "e23")}   # ellipse axes, as plot_ell
        for i, key in enumerate(("v1", "v2", "v3"), start=1):
            row = [f"V{i}", _fmt(stats[f"tau{i}"]), _fmt(stats[f"{key}_dec"], 1), _fmt(stats[f"{key}_inc"], 1)]
            if h is not None:
                a, b = pairs[key]
                row += [f"{_fmt(h[a], 1)}° / {_fmt(h[b], 1)}°"]
            if boot is not None:
                p = boot["params"]
                lo, hi = bounds[f"tau{i}"]
                row += [f"{_fmt(p[f'{key}_zeta'], 1)}° / {_fmt(p[f'{key}_eta'], 1)}°", f"{_fmt(lo)} – {_fmt(hi)}"]
            rows.append(row)
        html = _table(head, rows)
        if h is not None:
            source = "from this specimen's measurement scatter (σ, n)" if stats.get("specimen_hext") \
                else f"from the scatter of {stats['n']} tensors (ν = {stats['nf']})"
            ftests = (f"F = {_fmt(h['F'], 2)} (critical {h['F_crit']}) · F12 = {_fmt(h['F12'], 2)} · "
                      f"F23 = {_fmt(h['F23'], 2)} (critical {h['F12_crit']})")
            verdict = "anisotropic at 95%" if float(h["F"]) > float(h["F_crit"]) else "not distinguishable from isotropic at 95%"
            html += muted(f"Hext statistics {source}: {ftests} — {verdict}.")
        if boot is not None:
            kind = "parametric" if boot["parametric"] else "non-parametric"
            html += muted(f"{kind} bootstrap of {boot['n_bootstraps']} draws (seed {self.seed.value}); ellipses are "
                          f"dashed on the net, eigenvalue bounds are the 95% quantiles of the distributions.")
        self.table.object = html

    def _emit(self, stats: Optional[dict]) -> None:
        lines = preamble(self.s) + selection_lines(self.s)
        if stats is None or stats["n"] < 2:
            if stats is not None and stats.get("specimen_hext"):
                lines += ["row = tensors.iloc[0]",
                          "params = aniso.eigenparameters(row['s'])",
                          "hext = aniso.specimen_hext(row['s'], row['aniso_s_sigma'], row['aniso_s_n_measurements'], "
                          "row['aniso_type'])"]
            self.code.set(lines)
            return
        kwargs = dict(hext=self.hext.value, bootstrap=self.bootstrap.value)
        if self.bootstrap.value:
            kwargs.update(parametric=self.parametric.value, n_bootstraps=self.n_bootstraps.value,
                          random_seed=self.seed.value)
        lines.append(code.assign("stats", code.call("aniso.group_statistics", code.Name("list(tensors['s'])"), **kwargs)))
        if self.hext.value:
            lines.append("hext_ellipses = aniso.hext_ellipses(stats['hext'])       # (dec, inc) points about V1, V2, V3")
        if self.bootstrap.value:
            lines.append("boot_ellipses = aniso.bootstrap_ellipses(stats['hext'], stats['bootstrap']['params'])"
                         if self.hext.value else
                         "# bootstrap ellipses need the mean eigenvectors: rerun with hext=True")
            lines.append("tau_bounds = aniso.bootstrap_eigenvalue_bounds(stats['bootstrap']['taus'])")
        self.code.set(lines)

    def panel(self) -> pn.Column:
        widgets = (self.hext, self.bootstrap, self.parametric, self.n_bootstraps, self.seed, self.cloud,
                   self.compare, self.compare_dec, self.compare_inc)
        for w in widgets:
            w.align = "end"                       # checkboxes sit on the baseline of the slider and inputs
        options = pn.Row(*widgets)
        return pn.Column(options, self.summary, pn.Row(self.specimen_net, self.mean_net, self.cdf_box),
                         self.table, self.save.panel(), self.code.panel(), sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- shape
class ShapeView:
    """The shape of the fabric: Jelinek P′–T and Flinn F–L plots of the selection, with the mean tensor."""

    TYPE = "shape"

    def __init__(self, session):
        self.s = as_session(session)
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.jelinek = pn.pane.Bokeh()
        self.flinn = pn.pane.Bokeh()
        self.table = pn.pane.HTML("", sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.mean: Optional[dict] = None
        self.s.param.watch(lambda e: self.refresh(), WATCHED)
        self.refresh()

    def refresh(self) -> None:
        t = self.s.selection()
        if len(t) >= 2:
            self.mean = anisotropy.group_statistics(list(t["s"]), hext=False)
        elif len(t) == 1:
            self.mean = anisotropy.eigenparameters(t.iloc[0]["s"])
        else:
            self.mean = None
        self.jelinek.object = plots.jelinek_plot(t, self.mean)
        self.flinn.object = plots.flinn_plot(t, self.mean)
        label = self.s.selection_label()
        if self.mean is None:
            self.summary.object = kpi([label, ("specimens", 0)])
            self.table.object = ""
        else:
            m = self.mean
            shape = "oblate" if m["aniso_t"] > 0 else "prolate"
            self.summary.object = kpi([label, ("specimens", len(t)), ("P", _fmt(m["aniso_p"], 3)),
                                       ("P′", _fmt(m["aniso_pp"], 3)), ("T", f"{_fmt(m['aniso_t'], 3)} ({shape})"),
                                       ("L", _fmt(m["aniso_l"], 3)), ("F", _fmt(m["aniso_f"], 3))])
            names = {"aniso_p": "P = τ1/τ3", "aniso_pp": "P′ (Jelinek)", "aniso_t": "T (Jelinek)",
                     "aniso_l": "L = τ1/τ2", "aniso_f": "F = τ2/τ3", "aniso_ll": "ln L", "aniso_ff": "ln F",
                     "aniso_fl": "F/L", "aniso_vg": "Graham V (°)", "aniso_perc": "% anisotropy (τ1−τ3)/Σ",
                     "aniso_total": "% total (τ1−τ3)/mean"}
            rows = []
            for key, name in names.items():
                row = [name, _fmt(m[key], 3)]
                if len(t) >= 2:
                    row += [_fmt(t[key].min(), 3), _fmt(t[key].max(), 3)]
                rows.append(row)
            head = ["parameter", "mean tensor"] + (["min", "max"] if len(t) >= 2 else [])
            self.table.object = _table(head, rows) + muted(
                "Shape parameters of the mean tensor (not the mean of the specimens' parameters); "
                "min/max across the selected specimens. MagIC columns: " + ", ".join(names))
        lines = preamble(self.s) + selection_lines(self.s)
        if len(t) >= 2:
            lines.append("mean = aniso.group_statistics(list(tensors['s']), hext=False)   # shape parameters of the mean tensor")
        lines.append("shape = tensors[['specimen'] + aniso.SHAPE_COLUMNS]")
        self.code.set(lines)

    def panel(self) -> pn.Column:
        return pn.Column(self.summary, pn.Row(self.jelinek, self.flinn), self.table, self.code.panel(),
                         sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- specimens
class SpecimensView:
    """The tensor table of the selection: eigenparameters and shape of every specimen, in the chosen frame."""

    TYPE = "specimens"
    COLUMNS = ["specimen", "sample", "site", "aniso_type", "source", "tau1", "tau2", "tau3", "V1", "V2", "V3",
               "aniso_p", "aniso_pp", "aniso_t", "aniso_s_sigma", "aniso_s_n_measurements"]
    TITLES = {"aniso_type": "type", "tau1": "τ1", "tau2": "τ2", "tau3": "τ3", "V1": "V1 dec / inc",
              "V2": "V2 dec / inc", "V3": "V3 dec / inc", "aniso_p": "P", "aniso_pp": "P′", "aniso_t": "T",
              "aniso_s_sigma": "σ", "aniso_s_n_measurements": "n"}
    WIDTHS = {"specimen": 105, "sample": 90, "site": 70, "aniso_type": 60, "source": 65, "tau1": 65, "tau2": 65,
              "tau3": 65, "V1": 105, "V2": 105, "V3": 105, "aniso_p": 65, "aniso_pp": 65, "aniso_t": 65,
              "aniso_s_sigma": 65, "aniso_s_n_measurements": 40}

    def __init__(self, session):
        self.s = as_session(session)
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.table = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, disabled=True, pagination="local",
                                          page_size=25, sizing_mode="stretch_width", layout="fit_data_stretch",
                                          titles=self.TITLES, widths=self.WIDTHS, text_align={"specimen": "left", "sample": "left",
                                                                          "site": "left"})
        self.code = code.CodePane()
        self.s.param.watch(lambda e: self.refresh(), WATCHED)
        self.refresh()

    def refresh(self) -> None:
        t = self.s.selection().copy()
        for i in (1, 2, 3):                                     # one readable column per eigenvector
            t[f"V{i}"] = [f"{d:.1f} / {inc:.1f}" for d, inc in zip(t[f"v{i}_dec"], t[f"v{i}_inc"])]
        cols = [c for c in self.COLUMNS if c in t.columns]
        shown = t[cols].copy() if len(t) else pd.DataFrame(columns=cols)
        for c in shown.columns:
            if shown[c].dtype.kind == "f":
                shown[c] = shown[c].round(4)
        self.table.value = shown
        rotated = int((t["source"] == "rotated").sum()) if len(t) else 0
        items = [self.s.selection_label(), ("specimens", len(t))]
        if rotated:
            items.append(("rotated here", rotated))
        self.summary.object = kpi(items)
        lines = preamble(self.s) + selection_lines(self.s)
        lines.append("table = tensors[['specimen', 'sample', 'site', 'aniso_type', 'source'] + aniso.EIGEN_COLUMNS "
                     "+ aniso.SHAPE_COLUMNS]")
        self.code.set(lines)

    def panel(self) -> pn.Column:
        return pn.Column(self.summary, self.table, self.code.panel(), sizing_mode="stretch_width")


class ReduceView:
    """Anisotropy tensors from the directory's anisotropy measurements.

    ``anisotropy.reduce_measurements`` fits one tensor per specimen from its
    ``LP-AN-ARM`` (AARM) or ``LP-AN-TRM`` (ATRM) steps — the in-field moments,
    less the zero-field baseline measured before them when asked, against
    the field directions the table records — or from its ``LP-AN-MS`` (AMS)
    Kappabridge positions, one susceptibility each along ``meas_orient_phi/
    theta`` (the fifteen-position scheme when the table does not say; no
    baseline applies). The result is offered to
    ``specimens.txt`` through :class:`TableSave` (``add_tensors_to_specimens_table``:
    an existing tensor of the same type is replaced, a new specimen gets a
    row). A directory with measurements but no specimens table starts here.
    """

    TYPE = "reduce"
    COLUMNS = ["specimen", "aniso_s_n_measurements", "aniso_s_sigma", "aniso_ftest", "aniso_ftest_quality",
               "V1", "V2", "V3", "aniso_p", "aniso_t", "aniso_alt"]
    TITLES = {"aniso_s_n_measurements": "n", "aniso_s_sigma": "σ", "aniso_ftest": "F", "aniso_ftest_quality": "F test",
              "V1": "V1 dec / inc", "V2": "V2 dec / inc", "V3": "V3 dec / inc", "aniso_p": "P", "aniso_t": "T",
              "aniso_alt": "alteration %"}
    WIDTHS = {"specimen": 110, "aniso_s_n_measurements": 40, "aniso_s_sigma": 75, "aniso_ftest": 70,
              "aniso_ftest_quality": 60, "V1": 110, "V2": 110, "V3": 110, "aniso_p": 70, "aniso_t": 70,
              "aniso_alt": 90}

    def __init__(self, session):
        if isinstance(session, pd.DataFrame) and "aniso_s" not in session.columns:      # a measurements table
            self.s = Session(specimens=pd.DataFrame(columns=["specimen"]))
            self.s.measurements = session
        else:
            self.s = as_session(session)
        self.protocol = pn.widgets.Select(name="protocol", options=[], width=140)
        self.baseline = pn.widgets.Checkbox(name="subtract the zero-field baseline", value=True)
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.table = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, disabled=True, pagination="local",
                                          page_size=25, sizing_mode="stretch_width", layout="fit_data_stretch",
                                          titles=self.TITLES, widths=self.WIDTHS, text_align={"specimen": "left"})
        self.problems = pn.pane.HTML("", sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.save = TableSave(self.s, self.code, "tensors", table="specimens", app=APP,
                              label=lambda: f"{self.protocol.value} from measurements",
                              after_save=lambda path: self.s.reload())
        self.tensors = pd.DataFrame()
        self.failed: dict = {}
        self._quiet = False
        self.protocol.param.watch(lambda e: None if self._quiet else self.refresh(), "value")
        self.baseline.param.watch(lambda e: self.refresh(), "value")
        self.s.param.watch(lambda e: self.follow(), "version")
        self.follow()

    def set_parameters(self, **values) -> None:
        for name, value in values.items():
            getattr(self, name).value = value

    def follow(self) -> None:
        """New data: the protocols its measurements hold become the options."""
        kinds = list(self.s.protocols())
        self._quiet = True
        try:
            self.protocol.options = kinds
            if kinds and self.protocol.value not in kinds:
                self.protocol.value = kinds[0]
        finally:
            self._quiet = False
        self.refresh()

    def refresh(self) -> None:
        s = self.s
        kind = self.protocol.value
        lines = ["import pandas as pd", "import pmagpy.anisotropy as aniso", "import pmagpy.contribution_builder as cb", ""]
        if s.directory:
            lines += [code.assign("contribution", code.call("cb.Contribution", s.directory)),
                      "measurements = contribution.tables['measurements'].df"]
        else:
            lines.append("# measurements: the DataFrame this view was given")
        if not kind or s.measurements is None:
            self.tensors, self.failed = pd.DataFrame(), {}
            self.table.value = pd.DataFrame(columns=self.COLUMNS)
            self.problems.object = ""
            self.summary.object = muted("no AMS, AARM or ATRM measurements in this directory — the tensors in "
                                        "specimens.txt are what there is to look at")
            self.code.set(lines + ["# nothing to reduce: no LP-AN-MS / LP-AN-ARM / LP-AN-TRM rows in measurements"])
            self.save.decline("nothing to reduce")
            self.baseline.disabled = False
            return
        self.baseline.disabled = kind == "AMS"          # a Kappabridge position has no zero-field step
        kwargs = {} if kind == "AMS" else {"baseline": bool(self.baseline.value)}
        self.tensors, self.failed = anisotropy.reduce_measurements(s.measurements, kind, **kwargs)
        lines.append(code.assign("tensors, problems", code.call("aniso.reduce_measurements", code.Name("measurements"),
                                                                 kind, **kwargs)))
        self.code.set(lines)
        shown = self.tensors.copy()
        for i in (1, 2, 3):
            shown[f"V{i}"] = [":".join(cell.split(":")[1:]).replace(":", " / ") for cell in shown[f"aniso_v{i}"]] \
                if len(shown) else []
        cols = [c for c in self.COLUMNS if c in shown.columns]
        shown = shown[cols] if len(shown) else pd.DataFrame(columns=cols)
        for c in shown.columns:
            if shown[c].dtype.kind == "f":
                shown[c] = shown[c].round(4)
        self.table.value = shown
        index = s.index()
        existing = set(index.loc[index["aniso_type"].astype(str) == kind, "specimen"].astype(str)) if len(index) else set()
        replaced = int(self.tensors["specimen"].astype(str).isin(existing).sum()) if len(self.tensors) else 0
        items = [f"{kind} from measurements", ("specimens reduced", len(self.tensors))]
        if replaced:
            items.append((f"already in specimens.txt as {kind}", replaced))
        if self.failed:
            items.append(("not reduced", len(self.failed)))
        self.summary.object = kpi(items)
        self.problems.object = "" if not self.failed else muted(
            "not reduced: " + "; ".join(f"<b>{name}</b> — {reason}" for name, reason in self.failed.items()))
        if not len(self.tensors):
            self.save.decline("no specimen could be reduced — see the reasons above")
            return
        tensors, samples = self.tensors, s.samples
        save_lines = ["samples = contribution.tables['samples'].df if 'samples' in contribution.tables else None",
                      code.assign("specimens", code.call("aniso.add_tensors_to_specimens_table", code.Name("specimens"),
                                                         code.Name("tensors"), code.Name("samples")))]
        self.save.offer(lambda df: anisotropy.add_tensors_to_specimens_table(df, tensors, samples), save_lines,
                        self.code.text.splitlines())

    def panel(self) -> pn.Column:
        options = pn.Row(self.protocol, pn.Column(self.baseline, margin=(22, 0, 0, 10)), align="start")
        return pn.Column(options, self.summary, self.problems, self.table, self.save.panel(), self.code.panel(),
                         sizing_mode="stretch_width")


TABS = [("eigenvectors", "Eigenvectors", EigenvectorsView), ("shape", "Shape", ShapeView),
        ("specimens", "Specimens", SpecimensView), ("reduce", "Reduce", ReduceView)]

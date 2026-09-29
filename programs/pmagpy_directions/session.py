"""
The analysis session: one ``DemagData`` plus the interactive state that every
view shares (current specimen, coordinate system, projection, selected fit,
component colours) and the persistence policy (an auto-saved session file:
the fits and the step flags, restored when the dataset is opened again).
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import param

import pmagpy.demag as dc
from pmagpy import magic_project as mp

from pmagpy_panel import AppInfo, datasets, runtime
from pmagpy_panel.theme import ComponentColors

APP = AppInfo(name="PmagPy Directions", app_id=dc.APP_ID,
              # the older DEMAG_ names are still honoured
              env_prefixes=("PMAGPY_DIRECTIONS_", "DEMAG_"))


def env(name: str, default: str = "") -> str:
    """Environment setting ``PMAGPY_DIRECTIONS_<name>`` (the older ``DEMAG_<name>`` is still honoured)."""
    return datasets.env(name, APP.env_prefixes, default)


AUTOSAVE_NAME = f"{dc.APP_ID}_autosave.json"
# written by earlier builds of this app (fits only, as a .redo), read when there is no newer autosave
LEGACY_AUTOSAVE_NAMES = (f"{dc.APP_ID}_autosave.redo", "demag_v3_autosave.redo")
REDO_NAME = f"{dc.APP_ID}.redo"
# the recent list is shared by every PmagPy application; the per-application file
# earlier builds kept seeds it once
RECENT_FILE = env("RECENT", datasets.shared_recent_file(
    migrate_from=[os.path.join(os.path.expanduser("~"), f".{dc.APP_ID}_recent.json")]))

# this application's bindings of the shared helpers: the same behaviour for both
# applications, pointed at this one's recent list, output setting and test hook
looks_like_magic_dir = datasets.looks_like_magic_dir


def load_recent() -> list[str]:
    """Recently opened MagIC directories (most recent first), if the list exists."""
    return datasets.load_recent(RECENT_FILE)


def remember_recent(directory: str, limit: int = 12) -> list[str]:
    return datasets.remember_recent(RECENT_FILE, directory, limit)


def native_choose_directory(start: Optional[str] = None, prompt: str = "Choose a MagIC directory") -> Optional[str]:
    """The system folder chooser; ``PMAGPY_DIRECTIONS_CHOOSER_STUB`` answers it in tests."""
    return runtime.native_choose_directory(start, prompt, stub=env("CHOOSER_STUB"))


def native_chooser_available() -> bool:
    """True when a system folder dialog can be shown for this session (local browser)."""
    return runtime.native_chooser_available(stub=env("CHOOSER_STUB"))


def session_directory(default: str) -> str:
    """The directory this session opens: ``?dir=`` on the URL, then ``PMAGPY_DIRECTIONS_DIR``, then `default`."""
    return datasets.session_directory(APP.env_prefixes, default)


def default_output_dir(directory: str) -> str:
    """The data directory itself, or a folder of the dataset's own under ``PMAGPY_DIRECTIONS_OUTPUT`` when set."""
    return datasets.default_output_dir(directory, base=env("OUTPUT", ""))


_DATASETS: dict = {}          # directory -> (DemagData, (code stamp, table stamp)); shared by all browser sessions
AUTOSAVE_DELAY = 0.8          # seconds of quiet after an edit before the session file is written


def _server_document():
    """The Bokeh document of the served session this code runs in, or None outside one."""
    try:
        import panel as pn
        doc = pn.state.curdoc
    except Exception:
        return None
    if doc is not None and getattr(doc, "session_context", None) is not None:
        return doc
    return None


def _code_stamp() -> float:
    """Newest modification time of the app's source files (invalidates the cache after edits).

    Zero in a packaged build, where the sources are frozen into an archive and
    there is nothing on disk to date (the code cannot change under a running app).
    """
    here = os.path.dirname(os.path.abspath(__file__))
    core = os.path.dirname(os.path.abspath(dc.__file__))
    files = [os.path.join(core, "demag.py"), os.path.join(core, "demag_geo.py"), os.path.join(core, "magic_project.py")]
    if os.path.isdir(here):
        files += [os.path.join(here, f) for f in os.listdir(here) if f.endswith(".py")]
    stamps = [os.path.getmtime(f) for f in files if os.path.exists(f)]
    return max(stamps) if stamps else 0.0


class Session(param.Parameterized):
    """State shared by the views. Views watch the parameters below."""

    directory = param.String(default="", doc="MagIC directory that was loaded")
    output_dir = param.String(default="", doc="where .redo files, tables and figures are written")
    specimen = param.Selector(default=None, objects=[], doc="current specimen name")
    coord = param.Selector(default=dc.COORD_SPECIMEN, objects=list(dc.COORD_NAMES),
                           doc="MagIC dir_tilt_correction code")
    projection = param.Selector(default="nrm", objects=list(dc.PROJECTIONS), doc="Zijderveld projection")
    label_every = param.Selector(default=-1, objects={"auto": -1, "all": 1, "none": 0},
                                 doc="step labels: auto thins labels where symbols pile up")
    current = param.Parameter(default=None, doc="selected Component of the current specimen")
    unify_polarity = param.Boolean(default=True, doc="bring VGPs / location directions to a common polarity")
    flip_polarity = param.Boolean(default=False, doc="report the antipodes of the unified set")
    apply_criteria = param.Boolean(default=False, doc="judge fits and means by the directory's criteria.txt "
                                                      "(DE-SPEC / DE-SAMP / DE-SITE): failing rows are written "
                                                      "result_quality 'b' and left out of the level above")
    version = param.Integer(default=0, doc="incremented whenever interpretations or flags change")
    status = param.String(default="")

    def __init__(self, directory: Optional[str] = None, output_dir: Optional[str] = None, cache: bool = False,
                 **params):
        super().__init__(**params)
        self.data: Optional[dc.DemagData] = None
        self.colors = ComponentColors()
        self.autosave_enabled = True
        self.autosave_delay = AUTOSAVE_DELAY
        self._autosave_doc = None     # the Bokeh document holding a pending autosave, and its callback
        self._autosave_pending = None
        self.cache = cache            # reuse an already loaded dataset (its interpretations included)
        if directory:
            self.load(directory, output_dir)

    # ------------------------------------------------------------------ loading
    def load(self, directory: str, output_dir: Optional[str] = None) -> bool:
        """Open a MagIC directory; False (with the reason in ``status``) when it cannot be opened.

        Nothing about the session changes until the new dataset has been read
        and its fits restored: a directory that fails to open leaves the open
        dataset, its output directory and its fits exactly as they were.
        """
        directory = os.path.abspath(os.path.expanduser(directory))
        if not looks_like_magic_dir(directory):
            self.status = f"{directory} has no measurements.txt"
            return False
        self.flush_autosave()         # the dataset being left keeps its last edits
        output_dir = os.path.abspath(os.path.expanduser(output_dir)) if output_dir else default_output_dir(directory)
        stamp = (_code_stamp(), datasets.table_stamp(directory))
        cached = _DATASETS.get(directory) if self.cache else None
        try:
            if cached is not None and cached[1] == stamp:
                data, current, message = cached[0], None, f"{len(cached[0].components)} fits in memory"
            else:
                data = dc.DemagData.from_directory(directory)
                current, message = self._restore(data, directory, output_dir)
                if self.cache:
                    _DATASETS[directory] = (data, stamp)
        except Exception as exc:          # anything at all: the dataset is not opened, the open one is kept
            reason = str(exc) or type(exc).__name__
            self.status = f"Could not open {directory}: {reason}"
            return False
        self.output_dir = output_dir
        self.data = data
        data.set_criteria(data._table("criteria") if self.apply_criteria else None)   # a cached dataset may differ
        self.colors = ComponentColors()
        remember_recent(directory)
        for comp in data.components:
            if comp.color:
                self.colors.assign(comp.name, comp.color) if comp.name not in self.colors.as_dict() else None
        names = data.specimen_names
        self.param.specimen.objects = names
        n_warnings = len(data.warnings)
        if n_warnings:
            message += f"; {n_warnings} warning{'s' if n_warnings > 1 else ''} while reading (see Export → Log)"
        # one batched update: the views' watchers must see the new dataset, the new
        # specimen and the cleared selection together (a redraw in between would look
        # the old specimen name up in the new dataset)
        self.param.update(current=None, specimen=current if current in names else names[0], directory=directory,
                          coord=data.default_coord(),
                          status=f"{len(names)} specimens from {os.path.basename(directory.rstrip('/'))}; {message}",
                          version=self.version + 1)
        # re-opening the directory that is already open leaves `specimen` unchanged, so
        # its watcher does not run: the selected fit is settled here in every case
        self._sync_current()
        return True

    def _restore(self, data: dc.DemagData, directory: str, output_dir: str) -> tuple:
        """Bring back the interpretations of a freshly read dataset: ``(current specimen, message)``.

        In order: the autosave (the work in progress of this application), the
        interpretations stored in specimens.txt, the legacy Demag GUI's
        demag_gui.redo. An autosave that cannot be read is set aside (renamed,
        not deleted) and one that holds nothing is passed over; the message
        says where the fits came from and which other source exists.
        """
        notes = []
        stored = data.stored_interpretation_count()
        legacy = os.path.join(directory, "demag_gui.redo")
        spec_file = os.path.join(directory, "specimens.txt")
        for path in [os.path.join(output_dir, n) for n in (AUTOSAVE_NAME,) + LEGACY_AUTOSAVE_NAMES]:
            if not os.path.exists(path):
                continue
            name = os.path.basename(path)
            try:
                if path.endswith(".json"):
                    n, current = data.load_components(path)
                else:
                    n, current = data.read_redo(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                moved = datasets.set_aside(path)
                notes.append(f"the autosave {name} could not be read ({exc}) and was set aside as "
                             f"{os.path.basename(moved)}")
                continue
            if n == 0:
                notes.append(f"the autosave {name} held no fits and was passed over")
                continue
            message = f"restored {n} fits from the autosave"
            if stored:
                newer = os.path.exists(spec_file) and os.path.getmtime(spec_file) > os.path.getmtime(path)
                notes.append(f"specimens.txt holds {stored} interpretations{' and is newer' if newer else ''} "
                             "(Export → Import from specimens.txt replaces the restored fits with them)")
            return current, "; ".join([message] + notes)
        if stored and os.path.exists(legacy) and os.path.exists(spec_file) and \
                os.path.getmtime(legacy) > os.path.getmtime(spec_file):
            # the legacy GUI saved its .redo more often than it exported: the newer of the two is the later work
            try:
                n, current = data.read_redo(legacy)
            except (OSError, ValueError) as exc:
                n, current = 0, None
                notes.append(f"demag_gui.redo could not be read ({exc})")
            if n:
                return current, "; ".join([f"loaded {n} fits from demag_gui.redo, which is newer than specimens.txt "
                                           f"(its {stored} interpretations: Export → Import from specimens.txt)"]
                                          + notes)
            if not notes:
                notes.append("demag_gui.redo held no fits and was passed over")
            legacy = ""
        if stored:
            n = data.load_components_from_specimens_table()
            message = f"imported {n} fits from specimens.txt"
            if legacy and os.path.exists(legacy):
                notes.append("demag_gui.redo was not read (Export → Load .redo reads it)")
            return None, "; ".join([message] + notes)
        if legacy and os.path.exists(legacy):
            try:
                n, current = data.read_redo(legacy)
                return current, "; ".join([f"loaded {n} fits from demag_gui.redo"] + notes)
            except (OSError, ValueError) as exc:
                notes.append(f"demag_gui.redo could not be read ({exc})")
        return None, "; ".join(["no interpretations yet"] + notes)

    # ------------------------------------------------------------------ accessors
    @property
    def spec(self) -> dc.SpecimenData:
        return self.data.specimens[self.specimen]

    @property
    def ready(self) -> bool:
        """True when the current specimen belongs to the loaded dataset (false mid-switch)."""
        return self.data is not None and self.specimen in self.data.specimens

    @property
    def active_coord(self) -> int:
        """The requested coordinate system, or the best one below it that the specimen supports."""
        if not self.ready:
            return dc.COORD_SPECIMEN
        return self.data.best_coord(self.specimen, self.coord)

    def color_of(self, name: str) -> str:
        return self.colors(name)

    def set_color(self, name: str, color: str) -> None:
        """Change the colour of every fit called ``name``: all views, exports and the
        auto-saved .redo (which carries a colour per fit) follow."""
        if self.data is None or self.colors.as_dict().get(name) == color:
            return
        self.colors.assign(name, color)
        for comp in self.data.components:
            if comp.name == name:
                comp.color = color
        self._changed()

    def components(self, specimen: Optional[str] = None) -> list[dc.Component]:
        return self.data.components_for(specimen or self.specimen)

    def fits(self, specimen: Optional[str] = None, coord: Optional[int] = None):
        """[(Component, DirectionResult | None, colour)] for a specimen."""
        coord = self.active_coord if coord is None else coord
        return [(c, self.data.fit(c, coord), self.color_of(c.name)) for c in self.components(specimen)]

    def rotation(self) -> float:
        fit_dec = None
        if self.current is not None:
            res = self.data.fit(self.current, self.active_coord)
            if res is not None and res.direction_type == "l":
                fit_dec = res.dir_dec
        return dc.projection_rotation(self.spec, self.active_coord, self.projection, fit_dec)

    # ------------------------------------------------------------------ navigation
    def step_specimen(self, delta: int) -> None:
        names = self.param.specimen.objects
        self.specimen = names[(names.index(self.specimen) + delta) % len(names)]

    def _sync_current(self) -> None:
        comps = self.components()
        if self.current not in comps:
            self.current = comps[-1] if comps else None

    @param.depends("specimen", watch=True)
    def _on_specimen(self):
        self._sync_current()

    # ------------------------------------------------------------------ criteria
    def criteria_count(self) -> int:
        """How many rows of the directory's criteria.txt judge directions (0 = none to apply)."""
        if self.data is None:
            return 0
        table = self.data._table("criteria")
        if table is None:
            return 0
        names = set(dc.DemagData.CRITERION_NAMES.values())
        return int(table["criterion"].astype(str).str.strip().isin(names).sum()) if "criterion" in table.columns else 0

    @param.depends("apply_criteria", watch=True)
    def _on_criteria(self):
        if self.data is None:
            return
        self.data.set_criteria(self.data._table("criteria") if self.apply_criteria else None)
        self.version += 1                  # means, poles and the export follow; nothing to autosave

    # ------------------------------------------------------------------ editing
    def _changed(self) -> None:
        self.version += 1
        if self.autosave_enabled:
            self.request_autosave()

    def add_component(self, name: str, imin: int, imax: int, fit_type: str = "DE-BFL") -> dc.Component:
        comp = self.data.add_component(self.specimen, name or "A", imin, imax, fit_type,
                                       color=self.color_of(name or "A"))
        self.current = comp
        self._changed()
        return comp

    def update_component(self, comp: dc.Component, imin=None, imax=None, fit_type=None, name=None) -> bool:
        """Edit a fit in place (bounds clamped and ordered, names kept unique per specimen)."""
        n = self.data.specimens[comp.specimen].n_steps
        lo = comp.imin if imin is None else max(0, min(int(imin), n - 1))
        hi = comp.imax if imax is None else max(0, min(int(imax), n - 1))
        if lo > hi:
            lo, hi = hi, lo
        if name is not None and name != comp.name:
            if any(c.name == name for c in self.data.components_for(comp.specimen)):
                self.status = f"a fit named {name} already exists on {comp.specimen}"
                return False
            comp.name = name
            comp.color = self.color_of(name)
        comp.imin, comp.imax = lo, hi
        if fit_type is not None and fit_type in dc.FIT_TYPES:
            comp.fit_type = fit_type
        self._changed()
        return True

    def move_nearest_bound(self, comp: dc.Component, index: int) -> str:
        """Move whichever bound of ``comp`` is closer to ``index`` onto it; returns 'lower'/'upper'."""
        index = int(index)
        if index <= comp.imin or (index - comp.imin) < (comp.imax - index):
            self.update_component(comp, imin=min(index, comp.imax - 1))
            return "lower"
        self.update_component(comp, imax=max(index, comp.imin + 1))
        return "upper"

    def next_fit_name(self, specimen: Optional[str] = None) -> str:
        used = {c.name for c in self.components(specimen)}
        return next((ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch not in used), "fit")

    def delete_current(self) -> None:
        if self.current is not None:
            self.data.remove_component(self.current)
            self.current = None
            self._sync_current()
            self._changed()

    def delete_components(self, comps) -> None:
        for comp in list(comps):
            self.data.remove_component(comp)
        self._sync_current()
        self._changed()

    def toggle_current_quality(self) -> None:
        if self.current is not None:
            self.current.quality = "b" if self.current.quality == "g" else "g"
            self._changed()

    def toggle_component_quality(self, comp: dc.Component) -> None:
        comp.quality = "b" if comp.quality == "g" else "g"
        self._changed()

    def toggle_step(self, index: int, specimen: Optional[str] = None) -> str:
        new = self.data.toggle_step_quality(specimen or self.specimen, index)
        self._changed()
        return new

    def copy_current_to(self, specimens) -> int:
        """Apply the current fit's bounds (by treatment value) to other specimens."""
        if self.current is None:
            return 0
        spec = self.spec
        (vmin, umin), (vmax, umax) = self.data._si_bound(spec, self.current.imin), self.data._si_bound(spec, self.current.imax)
        n = 0
        for name in specimens:
            if name == self.specimen:
                continue
            imin = self.data.step_index_for_value(name, vmin, umin)
            imax = self.data.step_index_for_value(name, vmax, umax)
            if imin is None or imax is None or imax <= imin:
                continue
            self.data.add_component(name, self.current.name, imin, imax, self.current.fit_type,
                                    color=self.color_of(self.current.name))
            n += 1
        if n:
            self._changed()
        return n

    # ------------------------------------------------------------------ persistence
    @property
    def autosave_path(self) -> str:
        return os.path.join(self.output_dir, AUTOSAVE_NAME)

    def autosave(self) -> None:
        """Write the auto-saved session (fits and step flags) now."""
        self._autosave_pending = None
        if self.data is None or not self.autosave_enabled:
            return
        try:
            self.data.save_components(self.autosave_path, current_specimen=self.specimen)
        except OSError as exc:
            self.status = f"autosave failed: {exc}"

    def request_autosave(self) -> None:
        """Auto-save soon: once, ``autosave_delay`` seconds after the last edit.

        Writing the whole study's fits takes about a tenth of a second, which is
        most of what a bound nudge used to cost. Inside a served session the
        write is deferred on the session's document (so the file is written
        under the document lock, like any other change) and every edit within
        the delay restarts the clock; outside one — a script, a test — it
        happens at once.
        """
        doc = _server_document()
        if doc is None:
            self.autosave()
            return
        if self._autosave_pending is not None and self._autosave_doc is doc:
            try:
                doc.remove_timeout_callback(self._autosave_pending)
            except ValueError:
                pass
        self._autosave_doc = doc
        self._autosave_pending = doc.add_timeout_callback(self.autosave, int(self.autosave_delay * 1000))

    def flush_autosave(self) -> None:
        """Write a pending autosave now (before the dataset or the output directory changes)."""
        if self._autosave_pending is None:
            return
        try:
            self._autosave_doc.remove_timeout_callback(self._autosave_pending)
        except (ValueError, AttributeError):
            pass
        self.autosave()

    def save_redo(self, path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return self.data.write_redo(path, current_specimen=self.specimen)

    def load_redo(self, path: str, replace: bool = True) -> int:
        n, current = self.data.read_redo(path, replace=replace)
        for comp in self.data.components:
            if comp.color and comp.name not in self.colors.as_dict():
                self.colors.assign(comp.name, comp.color)
        if current in self.param.specimen.objects:
            self.specimen = current
        self._sync_current()
        self._changed()
        return n

    def import_from_specimens_table(self) -> int:
        n = self.data.load_components_from_specimens_table()
        self._sync_current()
        self._changed()
        return n

    def export_tables(self, coords=(dc.COORD_SPECIMEN, dc.COORD_GEOGRAPHIC, dc.COORD_TILT),
                      levels=("sample", "site", "location"), mean_coord: Optional[int] = None,
                      site_over: str = "specimens", write_measurements: bool = True,
                      analysts: Optional[str] = None, common_polarity: Optional[bool] = None,
                      flip: Optional[bool] = None, mean_coords=None) -> list[str]:
        """Write MagIC tables (and a .redo) to ``output_dir``; returns the paths written.

        Means and poles are written for every coordinate system in
        ``mean_coords`` (default: each of ``coords`` the dataset supports —
        geographic and tilt-corrected rows side by side, as the legacy GUI
        wrote them); ``mean_coord`` selects a single one instead.

        The tables are written all or nothing (:class:`pmagpy.magic_project.StagedExport`):
        a failure part way leaves the output directory as it was. Every table
        replaced is kept in ``backup_before_pmagpy_directions/previous/``, and
        when the output directory is the data directory itself the tables as
        they were before this application first wrote there are kept once in
        ``backup_before_pmagpy_directions/``. An output directory of its own
        also receives the source's other tables (ages, criteria, contribution,
        ...) so that it is a complete contribution.
        """
        self.flush_autosave()
        if mean_coords is None:
            mean_coords = (mean_coord,) if mean_coord is not None else self.default_mean_coords()
        common_polarity = self.unify_polarity if common_polarity is None else common_polarity
        flip = self.flip_polarity if flip is None else flip
        in_place = os.path.realpath(self.output_dir) == os.path.realpath(self.directory)
        stage = mp.StagedExport(self.output_dir, backup=os.path.join(self.output_dir, self.BACKUP_DIR),
                                originals=in_place)
        with stage:
            self.data.write_specimens(stage.dir, coords=coords, analysts=analysts)
            if write_measurements:
                self.data.write_measurements(stage.dir)
            for level in levels:
                over = {"site": site_over, "location": "sites"}.get(level, "specimens")
                self.data.write_means(level, stage.dir, coords=tuple(mean_coords), over=over, analysts=analysts,
                                      common_polarity=common_polarity, flip=flip)
            self.data.write_redo(os.path.join(stage.dir, REDO_NAME), current_specimen=self.specimen)
        written = list(stage.written)
        written += mp.copy_companion_tables(self.directory, self.output_dir, skip=written)
        self.last_backup = stage.backed_up
        return written

    def default_mean_coords(self) -> tuple:
        """Coordinate systems for means, VGPs and poles: geographic and tilt-corrected where the
        dataset supports them; specimen coordinates only for an unoriented collection (a VGP
        from specimen coordinates means nothing)."""
        coverage = self.data.coord_coverage() if self.data is not None else {}
        oriented = tuple(c for c in (dc.COORD_GEOGRAPHIC, dc.COORD_TILT) if coverage.get(c, 0) > 0)
        return oriented or (dc.COORD_SPECIMEN,)

    BACKUP_DIR = f"backup_before_{dc.APP_ID}"

    def validate_output(self) -> dict:
        """Validate the MagIC tables in the output directory with pmagpy's validator."""
        return dc.validate_directory(self.output_dir)

    # ------------------------------------------------------------------ summaries
    def study_summary(self) -> dict:
        n_fits = len(self.data.components)
        n_spec_with = len({c.specimen for c in self.data.components})
        return {"specimens": len(self.data.specimens), "interpreted": n_spec_with, "fits": n_fits,
                "sites": len(self.data.names_at("site")), "locations": len(self.data.names_at("location")),
                "components": self.data.component_names()}

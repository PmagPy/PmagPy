"""
The analysis session: one ``DemagData`` plus the interactive state that every
view shares (current specimen, coordinate system, projection, selected fit,
component colours) and the persistence policy (auto-saved ``.redo``).
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import param

import pmagpy.demag as dc

from .theme import ComponentColors

ENV_PREFIXES = ("PMAGPY_DIRECTIONS_", "DEMAG_")


def env(name: str, default: str = "") -> str:
    """Environment setting ``PMAGPY_DIRECTIONS_<name>`` (the older ``DEMAG_<name>`` is still honoured)."""
    for prefix in ENV_PREFIXES:
        value = os.environ.get(prefix + name)
        if value:
            return value
    return default


AUTOSAVE_NAME = f"{dc.APP_ID}_autosave.redo"
LEGACY_AUTOSAVE_NAMES = ("demag_v3_autosave.redo",)          # written by earlier builds of this app
REDO_NAME = f"{dc.APP_ID}.redo"
RECENT_FILE = env("RECENT", os.path.join(os.path.expanduser("~"), f".{dc.APP_ID}_recent.json"))


def load_recent() -> list[str]:
    """Recently opened MagIC directories (most recent first), if the list exists."""
    try:
        import json
        with open(RECENT_FILE) as fh:
            return [d for d in json.load(fh) if os.path.isdir(d)]
    except (OSError, ValueError):
        return []


def remember_recent(directory: str, limit: int = 12) -> list[str]:
    import json
    directory = os.path.abspath(directory)
    recent = [d for d in load_recent() if d != directory]
    recent.insert(0, directory)
    recent = recent[:limit]
    try:
        with open(RECENT_FILE, "w") as fh:
            json.dump(recent, fh, indent=1)
    except OSError:
        pass
    return recent


def native_choose_directory(start: Optional[str] = None, prompt: str = "Choose a MagIC directory") -> Optional[str]:
    """Open the operating system's folder chooser on the machine running the server.

    macOS uses an AppleScript ``choose folder`` dialog shown in the frontmost
    application, Linux uses ``zenity`` when available, Windows the .NET
    FolderBrowserDialog. Returns the chosen absolute path, or None when the
    dialog was cancelled or no chooser is available (remote sessions).
    """
    import subprocess
    import sys
    stub = env("CHOOSER_STUB")            # test hook: pretend the user picked this directory
    if stub:
        return stub
    start = start if start and os.path.isdir(start) else os.path.expanduser("~")
    try:
        if sys.platform == "darwin":
            script = (
                'tell application (path to frontmost application as text)\n'
                f'  set f to choose folder with prompt "{prompt}" default location POSIX file "{start}"\n'
                "end tell\n"
                "POSIX path of f"
            )
            out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=600)
            if out.returncode != 0:
                return None
            return out.stdout.strip().rstrip("/") or None
        if sys.platform.startswith("linux"):
            out = subprocess.run(["zenity", "--file-selection", "--directory", f"--title={prompt}",
                                  f"--filename={start}/"], capture_output=True, text=True, timeout=600)
            return out.stdout.strip() or None if out.returncode == 0 else None
        if sys.platform.startswith("win"):
            ps = ("Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog;"
                  f"$d.Description = '{prompt}'; $d.SelectedPath = '{start}';"
                  "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=600)
            return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def native_chooser_available() -> bool:
    """True when a system folder dialog can be shown for this session (local browser)."""
    import shutil
    import sys
    if env("CHOOSER_STUB"):
        return True
    try:
        import panel as pn
        req = pn.state.curdoc.session_context.request if pn.state.curdoc else None
        remote_ip = getattr(req, "remote_ip", None) if req else None
        if remote_ip and remote_ip not in ("127.0.0.1", "::1", "localhost"):
            return False
    except Exception:
        pass
    if sys.platform == "darwin":
        return shutil.which("osascript") is not None
    if sys.platform.startswith("linux"):
        return shutil.which("zenity") is not None and bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return sys.platform.startswith("win")


def looks_like_magic_dir(directory: str) -> bool:
    return os.path.isdir(directory) and os.path.exists(os.path.join(directory, "measurements.txt"))


def default_output_dir(directory: str) -> str:
    """The data directory itself, or <PMAGPY_DIRECTIONS_OUTPUT>/<dataset name> when that variable is set."""
    base = env("OUTPUT", "")
    if base:
        return os.path.join(base, os.path.basename(os.path.abspath(directory).rstrip("/")))
    return directory


_DATASETS: dict = {}          # directory -> (DemagData, code stamp); shared by all browser sessions


def _code_stamp() -> float:
    """Newest modification time of the app's source files (invalidates the cache after edits)."""
    here = os.path.dirname(os.path.abspath(__file__))
    core = os.path.dirname(os.path.abspath(dc.__file__))
    files = [os.path.join(core, "demag.py"), os.path.join(core, "demag_geo.py")] + \
            [os.path.join(here, f) for f in os.listdir(here) if f.endswith(".py")]
    return max(os.path.getmtime(f) for f in files if os.path.exists(f))


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
    version = param.Integer(default=0, doc="incremented whenever interpretations or flags change")
    status = param.String(default="")

    def __init__(self, directory: Optional[str] = None, output_dir: Optional[str] = None, cache: bool = False,
                 **params):
        super().__init__(**params)
        self.data: Optional[dc.DemagData] = None
        self.colors = ComponentColors()
        self.autosave_enabled = True
        self.cache = cache            # reuse an already loaded dataset (its interpretations included)
        if directory:
            self.load(directory, output_dir)

    # ------------------------------------------------------------------ loading
    def load(self, directory: str, output_dir: Optional[str] = None) -> bool:
        directory = os.path.abspath(os.path.expanduser(directory))
        if not looks_like_magic_dir(directory):
            self.status = f"{directory} has no measurements.txt"
            return False
        self.output_dir = output_dir or default_output_dir(directory)
        stamp = _code_stamp()
        cached = _DATASETS.get(directory) if self.cache else None
        if cached is not None and cached[1] == stamp:
            data, current, message = cached[0], None, f"{len(cached[0].components)} fits in memory"
        else:
            try:
                data = dc.DemagData.from_directory(directory)
            except Exception as exc:
                self.status = f"Could not load {directory}: {exc}"
                return False
            autosaves = [os.path.join(self.output_dir, n) for n in (AUTOSAVE_NAME,) + LEGACY_AUTOSAVE_NAMES]
            autosave = next((p for p in autosaves if os.path.exists(p)), None)
            legacy = os.path.join(directory, "demag_gui.redo")
            if autosave:
                n, current = data.read_redo(autosave)
                message = f"restored {n} fits from {os.path.basename(autosave)}"
            elif os.path.exists(legacy):
                n, current = data.read_redo(legacy)
                message = f"loaded {n} fits from demag_gui.redo"
            else:
                n = data.load_components_from_specimens_table()
                current = None
                message = f"imported {n} fits from specimens.txt"
            if self.cache:
                _DATASETS[directory] = (data, stamp)
        self.data = data
        self.colors = ComponentColors()
        remember_recent(directory)
        for comp in data.components:
            if comp.color:
                self.colors.assign(comp.name, comp.color) if comp.name not in self.colors.as_dict() else None
        names = data.specimen_names
        self.param.specimen.objects = names
        # one batched update: the views' watchers must see the new dataset, the new
        # specimen and the cleared selection together (a redraw in between would look
        # the old specimen name up in the new dataset)
        self.param.update(current=None, specimen=current if current in names else names[0], directory=directory,
                          coord=data.default_coord(),
                          status=f"{len(names)} specimens from {os.path.basename(directory.rstrip('/'))}; {message}",
                          version=self.version + 1)
        return True

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

    # ------------------------------------------------------------------ editing
    def _changed(self) -> None:
        self.version += 1
        if self.autosave_enabled:
            self.autosave()

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
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.data.write_redo(self.autosave_path, current_specimen=self.specimen)
        except OSError as exc:
            self.status = f"autosave failed: {exc}"

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

        When the output directory is the data directory itself, the tables
        about to be overwritten are copied once to ``backup_before_pmagpy_directions/``
        so that the original contribution can always be recovered.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        self.backup_originals(levels, write_measurements)
        written = []
        p = self.data.write_specimens(self.output_dir, coords=coords, analysts=analysts)
        if p:
            written.append(p)
        if write_measurements:
            p = self.data.write_measurements(self.output_dir)
            if p:
                written.append(p)
        if mean_coords is None:
            mean_coords = (mean_coord,) if mean_coord is not None else self.default_mean_coords()
        common_polarity = self.unify_polarity if common_polarity is None else common_polarity
        flip = self.flip_polarity if flip is None else flip
        for level in levels:
            over = {"site": site_over, "location": "sites"}.get(level, "specimens")
            p = self.data.write_means(level, self.output_dir, coords=tuple(mean_coords), over=over, analysts=analysts,
                                      common_polarity=common_polarity, flip=flip)
            if p:
                written.append(p)
        written.append(self.data.write_redo(os.path.join(self.output_dir, REDO_NAME),
                                            current_specimen=self.specimen))
        return written

    def default_mean_coords(self) -> tuple:
        """Coordinate systems for means, VGPs and poles: geographic and tilt-corrected where the
        dataset supports them; specimen coordinates only for an unoriented collection (a VGP
        from specimen coordinates means nothing)."""
        coverage = self.data.coord_coverage() if self.data is not None else {}
        oriented = tuple(c for c in (dc.COORD_GEOGRAPHIC, dc.COORD_TILT) if coverage.get(c, 0) > 0)
        return oriented or (dc.COORD_SPECIMEN,)

    BACKUP_DIR = f"backup_before_{dc.APP_ID}"

    def backup_originals(self, levels=("sample", "site", "location"), measurements: bool = True) -> list[str]:
        """Copy the source tables that an in-place export would overwrite (once)."""
        if os.path.realpath(self.output_dir) != os.path.realpath(self.directory):
            return []
        import shutil
        names = ["specimens.txt"] + [f"{lvl}s.txt" for lvl in levels] + (["measurements.txt"] if measurements else [])
        backup = os.path.join(self.output_dir, self.BACKUP_DIR)
        copied = []
        for name in names:
            src, dst = os.path.join(self.directory, name), os.path.join(backup, name)
            if os.path.exists(src) and not os.path.exists(dst):
                os.makedirs(backup, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(dst)
        return copied

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

"""
The analysis session: one ``PintData`` plus the interactive state every view
shares (current specimen, selected bounds, criteria, correction switches) and
the persistence policy (an auto-saved session file next to the data).
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

import numpy as np
import param

import pmagpy.paleointensity as pint
from pmagpy import pint_stats as ps

from pmagpy_panel import AppInfo, datasets

APP = AppInfo(name="PmagPy Intensity", app_id=pint.APP_ID,
              env_prefixes=("PMAGPY_INTENSITY_", "THELLIER_"))


def env(name: str, default: str = "") -> str:
    """Environment setting ``PMAGPY_INTENSITY_<name>`` (``THELLIER_<name>`` also works)."""
    return datasets.env(name, APP.env_prefixes, default)


AUTOSAVE_NAME = f"{pint.APP_ID}_autosave.json"
SESSION_NAME = f"{pint.APP_ID}_session.json"
REDO_NAME = f"{pint.APP_ID}.redo"
LEGACY_REDO_NAMES = ("thellier_gui.redo", "thellier_GUI.redo")
# the recent list is shared by every PmagPy application; the per-application file
# earlier builds of this one kept seeds it once
RECENT_FILE = env("RECENT", datasets.shared_recent_file(
    migrate_from=[os.path.join(os.path.expanduser("~"), f".{pint.APP_ID}_recent.json")]))

looks_like_magic_dir = datasets.looks_like_magic_dir


def load_recent() -> list:
    return datasets.load_recent(RECENT_FILE)


def remember_recent(directory: str, limit: int = 12) -> list:
    return datasets.remember_recent(RECENT_FILE, directory, limit)


def native_choose_directory(start: Optional[str] = None,
                            prompt: str = "Choose a MagIC directory") -> Optional[str]:
    """The system folder chooser; ``PMAGPY_INTENSITY_CHOOSER_STUB`` answers it in tests."""
    return datasets.native_choose_directory(start, prompt, stub=env("CHOOSER_STUB"))


def native_chooser_available() -> bool:
    return datasets.native_chooser_available(stub=env("CHOOSER_STUB"))


def session_directory(default: str) -> str:
    """The directory this session opens: ``?dir=`` on the URL, then ``PMAGPY_INTENSITY_DIR``, then `default`."""
    return datasets.session_directory(APP.env_prefixes, default)


def default_output_dir(directory: str) -> str:
    """The data directory, or ``<PMAGPY_INTENSITY_OUTPUT>/<dataset>`` when that is set."""
    return datasets.default_output_dir(directory, base=env("OUTPUT", ""))


_DATASETS: dict = {}        # directory -> (PintData, code stamp); shared by all browser sessions


def _code_stamp() -> float:
    """Newest modification time of the app's sources (invalidates the cache after edits)."""
    here = os.path.dirname(os.path.abspath(__file__))
    core = os.path.dirname(os.path.abspath(pint.__file__))
    files = [os.path.join(core, name) for name in
             ("paleointensity.py", "pint_stats.py", "magic_project.py", "tdt.py", "bicep.py")]
    files += [os.path.join(here, f) for f in os.listdir(here) if f.endswith(".py")]
    return max(os.path.getmtime(f) for f in files if os.path.exists(f))


class Session(param.Parameterized):
    """State shared by the views. Views watch the parameters below."""

    directory = param.String(default="", doc="MagIC directory that was loaded")
    output_dir = param.String(default="", doc="where sessions, tables and figures are written")
    specimen = param.Selector(default=None, objects=[], doc="current specimen name")
    criteria_name = param.Selector(default=pint.DEFAULT_CRITERIA,
                                   objects=list(pint.CRITERIA_SETS), doc="active criteria set")
    add_ziggie = param.Boolean(default=False, doc="add Ziggie <= 0.1 to the active criteria")
    normalize = param.Boolean(default=True, doc="normalise the Arai plot by the NRM")
    show_checks = param.Boolean(default=True, doc="draw pTRM, tail and additivity checks")
    version = param.Integer(default=0, doc="incremented whenever an interpretation or flag changes")
    status = param.String(default="")

    def __init__(self, directory: Optional[str] = None, output_dir: Optional[str] = None,
                 cache: bool = False, **params):
        super().__init__(**params)
        self.data: Optional[pint.PintData] = None
        self.autosave_enabled = True
        self.cache = cache
        self.bicep_results: dict = {}
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
            data = cached[0]
            message = f"{len(data.interpretations)} interpretations in memory"
        else:
            try:
                data = pint.PintData.from_directory(directory)
            except Exception as exc:
                self.status = f"Could not load {directory}: {exc}"
                self.data = None
                return False
            message = self._restore(data)
            if self.cache:
                _DATASETS[directory] = (data, stamp)
        self.data = data
        self.bicep_results = {}
        remember_recent(directory)
        names = data.specimen_names
        self.param.specimen.objects = names
        self.param.criteria_name.objects = list(pint.CRITERIA_SETS)
        interpreted = [n for n in names if n in data.interpretations]
        self.param.update(
            specimen=(interpreted or names)[0], directory=directory,
            criteria_name=data.criteria.name,
            status=(f"{len(names)} specimens from {os.path.basename(directory.rstrip('/'))}; {message}"),
            version=self.version + 1)
        return True

    def _restore(self, data: pint.PintData) -> str:
        """Bring back the last session, a legacy .redo, or the stored interpretations."""
        autosave = os.path.join(self.output_dir, AUTOSAVE_NAME)
        if os.path.exists(autosave):
            try:
                n = data.load_session(autosave)
                return f"restored {n} interpretations from {AUTOSAVE_NAME}"
            except Exception as exc:                      # a corrupt autosave must not block loading
                self.status = f"could not read {AUTOSAVE_NAME}: {exc}"
        for name in LEGACY_REDO_NAMES:
            path = os.path.join(data.directory, name)
            if os.path.exists(path):
                n, problems = data.read_redo(path)
                return f"loaded {n} interpretations from {name}"
        n, problems = data.import_from_specimens_table()
        return f"imported {n} interpretations from specimens.txt"

    # ------------------------------------------------------------------ accessors
    @property
    def ready(self) -> bool:
        return self.data is not None and self.specimen in self.data.specimens

    @property
    def spec(self) -> pint.PintSpecimen:
        return self.data.specimens[self.specimen]

    @property
    def arai(self):
        return self.spec.arai if self.ready else None

    @property
    def interpretation(self) -> Optional[pint.Interpretation]:
        return self.data.interpretations.get(self.specimen) if self.ready else None

    @property
    def result(self) -> Optional[pint.PintResult]:
        return self.data.result(self.specimen) if self.ready else None

    def bounds(self) -> Optional[tuple]:
        interp = self.interpretation
        return None if interp is None else (interp.imin, interp.imax)

    def statistics(self) -> dict:
        return self.data.statistics(self.specimen) if (self.ready and self.interpretation) else {}

    # ------------------------------------------------------------------ navigation
    def step_specimen(self, delta: int) -> None:
        names = self.param.specimen.objects
        if not names:
            return
        index = names.index(self.specimen) if self.specimen in names else 0
        self.specimen = names[(index + delta) % len(names)]

    def go_to(self, specimen: str) -> None:
        if specimen in self.param.specimen.objects:
            self.specimen = specimen

    # ------------------------------------------------------------------ editing
    def _changed(self) -> None:
        self.version += 1
        self.autosave()

    def set_bounds(self, imin: int, imax: int) -> None:
        if not self.ready:
            return
        self.data.set_interpretation(self.specimen, imin, imax)
        self._changed()

    def move_nearest_bound(self, index: int) -> str:
        """Move whichever bound is closer to ``index``; with none set, start one."""
        if not self.ready:
            return ""
        interp = self.interpretation
        if interp is None:
            last = self.arai.n - 1
            self.set_bounds(index, min(last, index + 3))
            return "new"
        if abs(index - interp.imin) <= abs(index - interp.imax):
            self.set_bounds(min(index, interp.imax), interp.imax)
            return "min"
        self.set_bounds(interp.imin, max(index, interp.imin))
        return "max"

    def nudge(self, which: str, delta: int) -> None:
        interp = self.interpretation
        if interp is None:
            return
        if which == "min":
            self.set_bounds(interp.imin + delta, interp.imax)
        else:
            self.set_bounds(interp.imin, interp.imax + delta)

    def delete_interpretation(self, specimen: Optional[str] = None) -> None:
        self.data.remove_interpretation(specimen or self.specimen)
        self._changed()

    def toggle_quality(self, specimen: Optional[str] = None) -> None:
        interp = self.data.interpretations.get(specimen or self.specimen)
        if interp is None:
            return
        interp.quality = "b" if interp.quality == "g" else "g"
        self.data.invalidate(specimen or self.specimen)
        self._changed()

    def toggle_step(self, sequence: int, specimen: Optional[str] = None) -> tuple:
        """Flag a measurement good/bad; returns (new flag, notes about the consequence)."""
        name = specimen or self.specimen
        flag, notes = self.data.toggle_step_quality(name, sequence)
        self._changed()
        return flag, notes

    def set_correction(self, kind: str, use: Optional[bool]) -> None:
        interp = self.interpretation
        if interp is None:
            return
        setattr(interp, f"use_{kind}", use)
        self.data.invalidate(self.specimen)
        self._changed()

    def auto_interpret(self, specimens: Optional[Iterable[str]] = None, progress=None) -> dict:
        out = self.data.auto_interpret_all(specimens=specimens, progress=progress)
        self._changed()
        return out

    def copy_bounds(self, level: str) -> tuple:
        """Copy the current bounds to the rest of the sample, site or study."""
        if not self.ready:
            return 0, []
        if level == "study":
            targets = self.data.specimen_names
        else:
            targets = self.data.specimens_in(level, getattr(self.spec, level))
        copied, skipped = self.data.copy_bounds(self.specimen, targets)
        self._changed()
        return copied, skipped

    # ------------------------------------------------------------------ criteria
    @param.depends("criteria_name", "add_ziggie", watch=True)
    def _apply_criteria(self) -> None:
        if self.data is None:
            return
        criteria = pint.CRITERIA_SETS[self.criteria_name]
        if self.add_ziggie:
            criteria = criteria.with_criterion("Ziggie", "<=", ps.ZIGGIE_CRITERION)
        self.data.set_criteria(criteria)
        self.version += 1

    # ------------------------------------------------------------------ persistence
    @property
    def autosave_path(self) -> str:
        return os.path.join(self.output_dir, AUTOSAVE_NAME)

    def autosave(self) -> None:
        if not (self.autosave_enabled and self.data is not None and self.output_dir):
            return
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.data.save_session(self.autosave_path)
        except OSError as exc:                             # a read-only directory must not block work
            self.status = f"could not auto-save: {exc}"

    def save_session(self, path: str) -> str:
        return self.data.save_session(path)

    def load_session(self, path: str) -> int:
        n = self.data.load_session(path)
        self.version += 1
        return n

    def save_redo(self, path: str) -> str:
        return self.data.write_redo(path)

    def load_redo(self, path: str) -> tuple:
        out = self.data.read_redo(path)
        self.version += 1
        return out

    def import_from_specimens_table(self) -> tuple:
        out = self.data.import_from_specimens_table()
        self.version += 1
        return out

    # ------------------------------------------------------------------ export
    BACKUP_TABLES = ("specimens.txt", "samples.txt", "sites.txt", "locations.txt",
                     "measurements.txt", "criteria.txt")

    def export_tables(self, analysts: str = "", levels=("site",), write_measurements: bool = True,
                      only_accepted: bool = False, weighted: bool = False) -> list:
        """Write the MagIC 3 tables to ``output_dir``; returns the paths written."""
        os.makedirs(self.output_dir, exist_ok=True)
        self.data.project.backup_originals(self.output_dir, self.BACKUP_TABLES)
        written = []
        path = self.data.write_specimens(self.output_dir, analysts=analysts,
                                         only_accepted=only_accepted)
        if path:
            written.append(path)
        for level in levels:
            path = self.data.write_group(self.output_dir, level=level, analysts=analysts,
                                         weighted=weighted)
            if path:
                written.append(path)
        if write_measurements:
            path = self.data.write_measurements(self.output_dir)
            if path:
                written.append(path)
        path = self.data.write_criteria(self.output_dir)
        if path:
            written.append(path)
        written.append(self.data.save_session(os.path.join(self.output_dir, SESSION_NAME)))
        written.append(self.data.write_redo(os.path.join(self.output_dir, REDO_NAME)))
        return written

    def validate_output(self) -> dict:
        return self.data.validate_output(self.output_dir)

    # ------------------------------------------------------------------ summary
    def study_summary(self) -> dict:
        if self.data is None:
            return {}
        results = self.data.results()
        accepted = [r for r in results if self.data.is_accepted(r)]
        return {"specimens": len(self.data.specimens),
                "interpreted": len(self.data.interpretations),
                "accepted": len(accepted),
                "sites": len(self.data.names_at("site")),
                "protocols": self.data.protocol_counts(),
                "anisotropy": len(self.data.anisotropy),
                "cooling_rate": len(self.data.cooling_rate),
                "nlt": len(self.data.nlt)}

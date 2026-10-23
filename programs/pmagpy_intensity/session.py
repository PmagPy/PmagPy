"""
The analysis session: one ``PintData`` plus the interactive state every view
shares (current specimen, selected bounds, criteria, correction switches) and
the persistence policy (an auto-saved session file next to the data).
"""
from __future__ import annotations

import json
import os
from typing import Iterable, Optional

import numpy as np
import param

import pmagpy.paleointensity as pint
from pmagpy import magic_project as mp
from pmagpy import pint_stats as ps

from pmagpy_panel import AppInfo, autosave as guard, datasets

APP = AppInfo(name="PmagPy Intensity", app_id=pint.APP_ID,
              env_prefixes=("PMAGPY_INTENSITY_", "THELLIER_"))


def env(name: str, default: str = "") -> str:
    """Environment setting ``PMAGPY_INTENSITY_<name>`` (``THELLIER_<name>`` also works)."""
    return datasets.env(name, APP.env_prefixes, default)


AUTOSAVE_NAME = f"{pint.APP_ID}_autosave.json"
#: the session an export writes beside its tables, which its specimens_export.py restores; only the
#: export writes it
SESSION_NAME = f"{pint.APP_ID}_session.json"
#: what *Save session* writes by default: SESSION_SAVE_PREFIX + the date (+ -2, -3 ... when taken)
SESSION_SAVE_PREFIX = f"{pint.APP_ID}_session_"
#: the session Show code writes for its code to load, where the autosave does not hold the session as
#: it is now (it could not be written, or another window wrote it)
CODE_SESSION_NAME = f"{pint.APP_ID}_code_session.json"
#: where that file goes when neither the study's folder nor an output base can take it: a folder per
#: study under the user's own PmagPy folder (``~/.pmagpy``, where the recent list is kept)
CODE_SESSION_HOME = os.path.join(os.path.expanduser("~"), ".pmagpy", pint.APP_ID, "code_sessions")
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
    """Where this study's working copy goes in the PmagPy folder, should it need one
    (``PMAGPY_APPS_OUTPUT``, default ``~/PmagPy``; see :func:`pmagpy_panel.datasets.working_directory`)."""
    return datasets.default_output_dir(directory, base=datasets.output_base())


_DATASETS: dict = {}        # directory -> (PintData, code stamp); shared by all browser sessions
AUTOSAVE_DELAY = 0.8        # seconds of quiet after an edit before the session file is written


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
    """Newest modification time of the app's sources (invalidates the cache after edits)."""
    here = os.path.dirname(os.path.abspath(__file__))
    core = os.path.dirname(os.path.abspath(pint.__file__))
    files = [os.path.join(core, name) for name in
             ("paleointensity.py", "pint_stats.py", "magic_project.py", "tdt.py", "bicep.py")]
    if os.path.isdir(here):                       # a packaged build has no source directory on disk
        files += [os.path.join(here, f) for f in os.listdir(here) if f.endswith(".py")]
    stamps = [os.path.getmtime(f) for f in files if os.path.exists(f)]
    return max(stamps) if stamps else 0.0


class Session(param.Parameterized):
    """State shared by the views. Views watch the parameters below."""

    directory = param.String(default="", doc="MagIC directory that was loaded (the working copy, when there is one)")
    source_directory = param.String(default="", doc="the study as the analyst chose it (differs from directory "
                                                    "when the applications work on a copy of it)")
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
        self.autosave_delay = AUTOSAVE_DELAY
        self._autosave_doc = None       # the document holding a pending autosave, and its callback
        self._autosave_pending = None
        self.cache = cache
        self.bicep_results: dict = {}
        self._opening = False           # True while load() shows the opened study's own settings
        if directory:
            self.load(directory, output_dir)

    # ------------------------------------------------------------------ loading
    def load(self, directory: str, output_dir: Optional[str] = None) -> bool:
        """Open a MagIC directory; False (with the reason in ``status``) when it cannot be opened.

        Nothing about the session changes until the new dataset has been read
        and its interpretations restored: a directory that fails to open
        leaves the open dataset, its output directory and its interpretations
        exactly as they were.
        """
        directory = os.path.abspath(os.path.expanduser(directory))
        if not looks_like_magic_dir(directory):
            self.status = f"{directory} has no measurements.txt"
            return False
        self.flush_autosave()           # the dataset being left keeps its last edits
        source = directory
        if not output_dir:
            # every application works on the same folder: the study itself, or -- for an example or a
            # study that cannot be written in place -- one working copy of it in the PmagPy folder
            try:
                directory = datasets.working_directory(source)
            except OSError as exc:
                self.status = f"Could not make a working copy of {source}: {exc}"
                return False
        source = datasets.working_copy_source(directory) or source
        output_dir = os.path.abspath(os.path.expanduser(output_dir)) if output_dir else directory
        stamp = (_code_stamp(), datasets.table_stamp(directory))
        cached = _DATASETS.get(directory) if self.cache else None
        autosave = os.path.join(output_dir, AUTOSAVE_NAME)
        try:
            if cached is not None and cached[1] == stamp and guard.guard_of(cached[0]).may_write(autosave):
                data = cached[0]
                message = f"{len(data.interpretations)} interpretations in memory"
            else:
                data = pint.PintData.from_directory(directory)
                guard.guard_of(data).read(autosave)
                message = self._restore(data, output_dir)
                if self.cache:
                    _DATASETS[directory] = (data, stamp)
            names = data.specimen_names
            if not names:
                raise ValueError("no specimens with paleointensity experiments")
        except Exception as exc:          # anything at all: the dataset is not opened, the open one is kept
            self.status = f"Could not open {directory}: {str(exc) or type(exc).__name__}"
            return False
        self.output_dir = output_dir
        self.data = data
        try:                                            # what an in-place export may keep as "originals"
            self._source_files = set(os.listdir(directory))
        except OSError:
            self._source_files = set()
        self.bicep_results = {}
        remember_recent(source)                         # the study the analyst chose, not its copy
        self.param.specimen.objects = names
        self.param.criteria_name.objects = list(pint.CRITERIA_SETS)
        interpreted = [n for n in names if n in data.interpretations]
        n_warnings = len(data.warnings) + len(data.project.warnings)
        if n_warnings:
            message += f"; {n_warnings} warning{'s' if n_warnings > 1 else ''} while reading"
        restored = data.criteria
        if restored.name == "This study" and data.study_criteria is None:
            data.study_criteria = restored          # a session saved under this study's own criteria
        try:
            preset = data.criteria_named(restored.name)
        except KeyError:
            preset = None
        ziggie = (preset is not None and restored is not preset
                  and any(c.key == "Ziggie" for c in restored.specimen)
                  and not any(c.key == "Ziggie" for c in preset.specimen))
        self._opening = True
        try:
            self.param.update(
                specimen=(interpreted or names)[0], directory=directory, source_directory=source,
                criteria_name=restored.name, add_ziggie=ziggie,
                status=(f"{len(names)} specimens from {datasets.study_name(directory)}; {message}"),
                version=self.version + 1)
        finally:
            self._opening = False
        if data.criteria is not restored:
            # the criteria the session was saved under win over the preset of that name
            data.set_criteria(restored)
        return True

    def _restore(self, data: pint.PintData, output_dir: str) -> str:
        """Bring back the last session, the stored interpretations, or a legacy .redo; says which.

        An autosave that cannot be read is set aside (renamed, not deleted) and
        one that holds nothing is passed over. The stored interpretations in
        specimens.txt come before a legacy Thellier GUI .redo, as they do in
        MagIC; the message names any other source that exists.
        """
        notes = []
        autosave = os.path.join(output_dir, AUTOSAVE_NAME)
        legacy = [n for n in LEGACY_REDO_NAMES if os.path.exists(os.path.join(data.directory, n))]
        if os.path.exists(autosave):
            try:
                n = data.load_session(autosave)
                held = len(getattr(data, "_set_aside", {}))
                if n or held or data.step_flag_changes():
                    # interpretations, fits set aside by a bad-step flag, or flags: work, not an empty file
                    extra = f" and {held} set aside by a flag" if held else ""
                    return "; ".join([f"restored {n} interpretations{extra} from the autosave"] + notes)
                notes.append("the autosave held no interpretations and was passed over")
            except (OSError, ValueError, KeyError, TypeError) as exc:
                moved = datasets.set_aside(autosave)
                notes.append(f"the autosave could not be read ({exc}) and was set aside as "
                             f"{os.path.basename(moved)}")
        n, problems = data.import_from_specimens_table()
        if n:
            if legacy:
                notes.append(f"{legacy[0]} was not used: the stored interpretations come first, as the legacy "
                             "Thellier GUI reads them over its .redo (Export → Load .redo reads it)")
            return "; ".join([f"imported {n} interpretations from specimens.txt"] + notes)
        for name in legacy:
            try:
                n, problems = data.read_redo(os.path.join(data.directory, name))
                return "; ".join([f"loaded {n} interpretations from {name}"] + notes)
            except (OSError, ValueError) as exc:
                notes.append(f"{name} could not be read ({exc})")
        return "; ".join(["no interpretations yet"] + notes)

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
        self.request_autosave()

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

    def set_study_correction(self, kind: str, use: Optional[bool]) -> int:
        """Set a correction for every specimen (and every interpretation made later); returns how many changed."""
        if self.data is None:
            return 0
        changed = self.data.set_study_correction(kind, use)
        self._changed()
        return changed

    def auto_interpret(self, specimens: Optional[Iterable[str]] = None, progress=None,
                       replace: bool = False) -> dict:
        """Auto-interpret the specimens without an interpretation (``replace=True``: every one)."""
        out = self.data.auto_interpret_all(specimens=specimens, progress=progress, replace=replace)
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
        # "This study" is this study's own table, not the last one any session in the server read
        criteria = self.data.criteria_named(self.criteria_name)
        if criteria is None:
            self.status = "this study has no criteria table of its own"
            self.criteria_name = self.data.criteria.name if self.data.criteria.name in \
                self.param.criteria_name.objects else pint.DEFAULT_CRITERIA
            return
        if self.add_ziggie:
            criteria = criteria.with_criterion("Ziggie", "<=", ps.ZIGGIE_CRITERION)
        changed = criteria is not self.data.criteria
        self.data.set_criteria(criteria)
        self.version += 1
        if changed and not self._opening:
            # the analyst's choice is part of the session, as an edit is (opening a study writes nothing)
            self.request_autosave()

    # ------------------------------------------------------------------ persistence
    @property
    def autosave_path(self) -> str:
        return os.path.join(self.output_dir, AUTOSAVE_NAME)

    def autosave(self) -> None:
        """Write the session file now.

        Not when another window has written it since this dataset read or wrote it
        (:mod:`pmagpy_panel.autosave`): the header says so and the edits stay in memory.
        """
        self._autosave_pending = None
        if not (self.autosave_enabled and self.data is not None and self.output_dir):
            return
        keeper = guard.guard_of(self.data)
        if not keeper.may_write(self.autosave_path):
            self._another_window()
            return
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.data.save_session(self.autosave_path, writer=keeper.writer)
            keeper.wrote(self.autosave_path)
        except OSError as exc:                             # a read-only directory must not block work
            self.status = f"could not auto-save into {self.output_dir}: {exc.strerror or exc}"

    def _another_window(self) -> None:
        """Say that another window has the study's autosave, and let a reload read the study again."""
        self.status = guard.refusal_of(self.data)
        cached = _DATASETS.get(self.directory)
        if cached is not None and cached[0] is self.data:
            del _DATASETS[self.directory]

    def request_autosave(self) -> None:
        """Auto-save soon: once, ``autosave_delay`` seconds after the last edit.

        Inside a served session the write is deferred on the session's document
        (under the document lock, like any other change) and every edit within
        the delay restarts the clock, so nudging a bound does not rewrite the
        whole study's session file at every key press; outside a session it
        happens at once.
        """
        if not self.autosave_enabled:
            return
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

    def _holds_the_session(self, path: str) -> bool:
        """True when loading the session file at ``path`` would bring back the session as it is now."""
        try:
            with open(path, encoding="utf-8") as fh:
                saved = json.load(fh)
        except (OSError, ValueError):
            return False
        saved.pop("writer", None)
        return saved == json.loads(self.data.to_json())

    def code_session_folders(self) -> list:
        """Where a session snapshot for Show code may go, in order of preference.

        The study's own folder (the output directory, where the autosave goes), then the study's
        folder under the output base, then one under :data:`CODE_SESSION_HOME`. Never a folder that
        ships with PmagPy (the application bundle, a checkout's ``data_files``).
        """
        base = datasets.output_base()
        folders = [self.output_dir]
        if base:
            folders.append(datasets.default_output_dir(self.directory, base))
        folders.append(datasets.default_output_dir(self.directory, CODE_SESSION_HOME))
        shipped = datasets.shipped_roots()
        out = []
        for folder in folders:
            if not folder:
                continue
            real = os.path.realpath(folder)
            if any(real == root or real.startswith(root + os.sep) for root in shipped) or real in out:
                continue
            out.append(real)
        return out

    def code_session_file(self) -> tuple:
        """The session file Show code loads, and a note saying why it is not the autosave ("" when it is).

        An autosave that is due (or, with autosaving on, behind the session) is written first. When
        the autosave holds the session as it is now, it is the file; otherwise (it could not be
        written, autosaving is off, or another window wrote it) the session is written now to
        :data:`CODE_SESSION_NAME` in the first of :meth:`code_session_folders` that takes it.

        A window whose working copy was set aside writes nothing, here or elsewhere: its autosave and
        export do not either, and the window is to be reloaded.

        Raises:
            WorkingCopyReplaced: this window's working copy was set aside and a new one made in its place.
            OSError: no folder could take the file.
        """
        guard.guard_of(self.data).check(self.output_dir)
        if self._holds_the_session(self.autosave_path):
            return self.autosave_path, ""
        if self._autosave_pending is not None:
            self.flush_autosave()
        elif self.autosave_enabled:
            self.autosave()
        if self._holds_the_session(self.autosave_path):
            return self.autosave_path, ""
        why = ("the autosave holds an earlier state of the session" if os.path.exists(self.autosave_path)
               else f"there is no autosave in {datasets.shorten_home(self.output_dir)}")
        error = None
        for folder in self.code_session_folders():
            target = os.path.join(folder, CODE_SESSION_NAME)
            try:
                os.makedirs(folder, exist_ok=True)
                self.save_session(target)
                return target, why
            except guard.WorkingCopyReplaced:
                raise
            except OSError as exc:
                error = exc
        raise error or OSError("no folder could take the session file")

    def flush_autosave(self) -> None:
        """Write a pending autosave now (before the dataset or the output directory changes)."""
        if self._autosave_pending is None:
            return
        try:
            self._autosave_doc.remove_timeout_callback(self._autosave_pending)
        except (ValueError, AttributeError):
            pass
        self.autosave()

    def save_session(self, path: str) -> str:
        guard.guard_of(self.data).check(os.path.dirname(os.path.abspath(path)))
        return self.data.save_session(path)

    def default_session_name(self, today=None) -> str:
        """The file *Save session* writes unless given a name: ``pmagpy_intensity_session_<date>.json``,
        with ``-2``, ``-3`` ... added when that is taken. Never the export's own session file."""
        import datetime
        stem = SESSION_SAVE_PREFIX + (today or datetime.date.today()).isoformat()
        name, k = f"{stem}.json", 1
        while os.path.exists(os.path.join(self.output_dir, name)):
            k += 1
            name = f"{stem}-{k}.json"
        return name

    def session_files(self) -> list:
        """The sessions in the output directory that *Load session* offers, newest first: the export's
        own and every saved one (other applications' files, BiCEP draws and the autosave are not)."""
        try:
            names = os.listdir(self.output_dir)
        except OSError:
            return []
        found = []
        for name in names:
            if not name.endswith(".json") or name.startswith(".") or name == AUTOSAVE_NAME:
                continue
            if name.startswith(f"{pint.APP_ID}_session") or not name.startswith(("pmagpy_", "bicep_")):
                path = os.path.join(self.output_dir, name)
                try:
                    found.append((os.path.getmtime(path), name))
                except OSError:
                    continue
        return [name for _, name in sorted(found, reverse=True)]

    def load_session(self, path: str) -> int:
        n = self.data.load_session(path)
        self.version += 1
        return n

    def save_redo(self, path: str) -> str:
        guard.guard_of(self.data).check(os.path.dirname(os.path.abspath(path)))
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
    def export_tables(self, analysts: str = "", levels=("site",), write_measurements: bool = True,
                      only_accepted: bool = False, weighted: bool = False) -> list:
        """Write the MagIC 3 tables to ``output_dir``; returns the paths written.

        All or nothing (:class:`pmagpy.magic_project.StagedExport`): a failure
        part way leaves the output directory as it was. Every file replaced is
        kept in ``backup_before_pmagpy_intensity/previous/``, and in place the
        tables as they were before this application first wrote there are
        kept once in ``backup_before_pmagpy_intensity/``. A separate output
        directory also receives the source's other tables.
        """
        guard.guard_of(self.data).check(self.directory)
        self.flush_autosave()
        # merge into the tables as they are now, not as they were when the study
        # was opened: PmagPy Directions (or another browser session) may have
        # written its results into them since
        self.data.project.refresh_tables(self.output_dir, ("specimens", "samples", "sites",
                                                           "locations", "criteria"))
        # the site coordinates behind the VADMs are the one value read from those tables
        # that the export uses again (the hierarchy is kept as it was when the study opened)
        self.data.site_coords = mp.build_site_coords(self.data._table("sites"), self.data._table("samples"))
        in_place = os.path.realpath(self.output_dir) == os.path.realpath(self.directory)
        stage = mp.StagedExport(self.output_dir, backup=os.path.join(self.output_dir,
                                                                     self.data.project.backup_dir_name()),
                                originals=self._originals() if in_place else False,
                                keep_protected=in_place and not self._in_working_copy())
        with stage:
            self.data.write_specimens(stage.dir, analysts=analysts, only_accepted=only_accepted)
            for level in levels:
                self.data.write_group(stage.dir, level=level, analysts=analysts, weighted=weighted)
            measurements = self.data.write_measurements(stage.dir) if write_measurements else None
            self.data.write_criteria(stage.dir)
            self.data.save_session(os.path.join(stage.dir, SESSION_NAME))
            self.data.write_redo(os.path.join(stage.dir, REDO_NAME))
        written = list(stage.written)
        if stage.protected:
            self.data.warnings.append(mp.protected_message(stage.protected))
        refused = write_measurements and (measurements is None or os.path.basename(measurements)
                                          not in {os.path.basename(p) for p in written})
        if in_place and write_measurements and not refused:
            self.data.flags_written()        # the study's file now has these flags: later changes count from them
        if in_place and not refused:
            self._share_after_export()
        skip = written + (["measurements.txt"] if refused else [])
        written += mp.copy_companion_tables(self.directory, self.output_dir, skip=skip)
        self.last_backup = stage.backed_up
        return written

    def _share_after_export(self) -> None:
        """After an export into the study, the tables on disk are this dataset's own: a browser tab
        opened from now on shares it, as tabs opened before the export do, instead of reading the
        study again and keeping a second copy whose autosave would overwrite this one's."""
        cached = _DATASETS.get(self.directory)
        if self.cache and cached is not None and cached[0] is self.data:
            _DATASETS[self.directory] = (self.data, (_code_stamp(), datasets.table_stamp(self.directory)))

    def writes_in_place(self) -> bool:
        """True when an export replaces the study's own tables (the output directory is the data directory)."""
        return bool(self.directory) and os.path.realpath(self.output_dir) == os.path.realpath(self.directory)

    def _in_working_copy(self) -> bool:
        """True when the study is worked on in a working copy, whose tables are the applications' own."""
        return bool(self.source_directory) and \
            os.path.realpath(self.source_directory) != os.path.realpath(self.directory)

    def _originals(self) -> set:
        """The study's own tables as it was opened (not this application's .redo or session files)."""
        return {n for n in getattr(self, "_source_files", set())
                if n.endswith(".txt") and not n.startswith(pint.APP_ID)}

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

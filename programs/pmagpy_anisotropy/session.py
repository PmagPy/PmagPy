"""
The session: the anisotropy tensors of one MagIC directory and the selection
the views share — which specimens (a site, a sample, a location, all of them),
in which coordinate frame, of which anisotropy type.

The tensors live in ``specimens.txt`` (``aniso_s``), written there by the
converters (AMS from a Kappabridge) or by ``aarm_magic``/``atrm_magic`` from
measurements; the session reads the directory through ``MagicProject`` like
the other applications and keeps the tables. Everything computed from them
is ``pmagpy.anisotropy``'s, so a session can also be made from DataFrames
already in memory — that is how the views render inside a notebook.
"""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import param

from pmagpy import anisotropy
from pmagpy.magic_project import MagicProject, natural_key
from pmagpy_panel import AppInfo, datasets

APP = AppInfo(name="PmagPy Anisotropy", app_id="pmagpy_anisotropy", env_prefixes=("PMAGPY_ANISOTROPY_",))

ALL = "all specimens"                       # the group that is the whole table
LEVELS = {"site": "site", "sample": "sample", "location": "location"}   # grouping columns, in the picker's order


def env(name: str, default: str = "") -> str:
    """Environment setting ``PMAGPY_ANISOTROPY_<name>``."""
    return datasets.env(name, APP.env_prefixes, default)


RECENT_FILE = env("RECENT", datasets.shared_recent_file())


def session_directory(default: str) -> str:
    """The directory this session opens: ``?dir=`` on the URL, then ``PMAGPY_ANISOTROPY_DIR``, then `default`."""
    return datasets.session_directory(APP.env_prefixes, default)


def has_specimens(directory: str) -> bool:
    """The directory has a specimens table."""
    return os.path.isdir(directory) and os.path.exists(os.path.join(directory, "specimens.txt"))


def has_anisotropy_measurements(directory: str) -> bool:
    """The directory's measurements table has anisotropy-protocol rows (``LP-AN-…`` method codes)."""
    path = os.path.join(directory, "measurements.txt")
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8", errors="replace") as fh:
        return any("LP-AN-" in line for line in fh)


def can_open(directory: str) -> bool:
    """A directory the application can open: tensors to look at, or measurements to reduce into them."""
    return has_specimens(directory) or has_anisotropy_measurements(directory)


class Session(param.Parameterized):
    """State shared by the views; views watch ``directory`` and the selection parameters."""

    directory = param.String(default="", doc="MagIC directory that was loaded ('' for in-memory data)")
    coordinates = param.Selector(default="s", objects=list(anisotropy.COORDINATES), doc="s, g or t")
    level = param.Selector(default="site", objects=[*LEVELS], doc="what a group is")
    group = param.String(default=ALL, doc="the group being looked at, or ALL")
    aniso_type = param.String(default="", doc="AMS / AARM / ATRM ...; '' for every type")
    status = param.String(default="")
    version = param.Integer(default=0, doc="bumped whenever the tables change (a load, a reload after a save)")

    def __init__(self, directory: Optional[str] = None, specimens: Optional[pd.DataFrame] = None,
                 samples: Optional[pd.DataFrame] = None, sites: Optional[pd.DataFrame] = None, **params):
        super().__init__(**params)
        self.project: Optional[MagicProject] = None
        self.specimens: Optional[pd.DataFrame] = None
        self.samples: Optional[pd.DataFrame] = None
        self.sites: Optional[pd.DataFrame] = None
        self.measurements: Optional[pd.DataFrame] = None
        self._tensors: dict = {}                       # coordinates -> tensor_table, built on demand
        if specimens is not None:
            self.set_tables(specimens, samples, sites, status=f"{len(specimens)} specimen rows in memory")
        elif directory:
            self.load(directory)

    # ------------------------------------------------------------------ loading
    def load(self, directory: str) -> bool:
        """Read `directory`; False (with ``status`` saying why) when it cannot be read."""
        directory = os.path.abspath(os.path.expanduser(directory))
        if not can_open(directory):
            self.status = f"{directory} has no specimens.txt and no anisotropy measurements"
            return False
        try:
            project = MagicProject.from_directory(directory, app_id=APP.app_id)
            specimens = project.table("specimens")
            measurements = project.table("measurements")
        except Exception as ex:                                            # a malformed table is reported, not raised
            self.status = f"could not read {directory}: {ex}"
            return False
        if specimens is None and measurements is None:
            self.status = f"{directory}: specimens.txt is empty"
            return False
        self.project = project
        self.measurements = measurements
        self.set_tables(specimens if specimens is not None else pd.DataFrame(columns=["specimen"]),
                        project.table("samples"), project.table("sites"))
        self.directory = directory
        self.status = self.describe()
        return True

    def reload(self) -> bool:
        """Re-read the directory's tables after a save, keeping the selection where it still applies."""
        if self.project is None:
            return False
        keep = {"coordinates": self.coordinates, "level": self.level, "group": self.group,
                "aniso_type": self.aniso_type}
        project = self.project
        specimens = project.table("specimens")
        self.measurements = project.table("measurements")
        self.set_tables(specimens if specimens is not None else pd.DataFrame(columns=["specimen"]),
                        project.table("samples"), project.table("sites"))
        if keep["group"] in self.groups(keep["level"]):
            self.level, self.group = keep["level"], keep["group"]
        if keep["aniso_type"] in self.types():
            self.aniso_type = keep["aniso_type"]
        if self.frame_counts()[keep["coordinates"]]:
            self.coordinates = keep["coordinates"]
        self.status = self.describe()
        self.param.trigger("directory")        # the same directory with new contents: the chooser's counts follow
        return True

    def describe(self) -> str:
        """The status line: the tensors in the table, or the measurements waiting to be reduced."""
        n = self.n_specimens()
        protocols = self.protocols()
        waiting = " · ".join(f"{count} specimens with {kind} measurements" for kind, count in protocols.items())
        if not n:
            if protocols:
                return f"{self.directory or 'this directory'}: no tensors yet — {waiting} (Reduce)"
            return f"{self.directory}: no anisotropy tensors (aniso_s) in specimens.txt"
        types = ", ".join(self.types()) or "untyped"
        frames = self.frames()
        return (f"{n} specimens with tensors ({types}) · {frames['s']} specimen"
                f" / {frames['g']} geographic / {frames['t']} tilt-corrected")

    def protocols(self) -> dict:
        """Specimens with measurements of each reducible protocol, ``{'AARM': n, 'ATRM': n}``."""
        m = self.measurements
        if m is None or not len(m) or "method_codes" not in m.columns:
            return {}
        out = {}
        codes = m["method_codes"].fillna("").astype(str)
        for kind, protocol in anisotropy.PROTOCOLS.items():
            n = int(m.loc[codes.str.contains(protocol["code"], regex=False), "specimen"].nunique())
            if n:
                out[kind] = n
        return out

    def set_tables(self, specimens: pd.DataFrame, samples: Optional[pd.DataFrame] = None,
                   sites: Optional[pd.DataFrame] = None, status: str = "") -> None:
        """Take the tables as the session's data (a notebook's, or a directory's) and reset the selection."""
        self.specimens = specimens.reset_index(drop=True)
        self.samples = samples.reset_index(drop=True) if samples is not None else None
        self.sites = sites.reset_index(drop=True) if sites is not None else None
        self._tensors = {}
        if status:
            self.status = status
        self._reset_selection()
        self.version += 1

    def _reset_selection(self) -> None:
        counts = self.frame_counts()
        if not counts[self.coordinates] and any(counts.values()):
            self.coordinates = max(counts, key=counts.get)        # the frame most of the table is in
        index = self.index()
        levels = [level for level in LEVELS if index[level].notna().any()] if len(index) else []
        if self.level not in levels:
            self.level = levels[0] if levels else "site"
        self.group = ALL                                          # new data: start from the whole table
        if self.aniso_type not in self.types():
            self.aniso_type = ""

    # ------------------------------------------------------------------ the tensors
    def tensors(self, coordinates: Optional[str] = None) -> pd.DataFrame:
        """Every specimen's tensor in a frame (``anisotropy.tensor_table``), cached per frame."""
        coordinates = coordinates or self.coordinates
        if coordinates not in self._tensors:
            self._tensors[coordinates] = anisotropy.tensor_table(self.specimens, self.samples, coordinates)
        return self._tensors[coordinates]

    def frames(self) -> dict:
        """Specimens with a tensor row in each frame, ``{'s': n, 'g': n, 't': n}``."""
        return anisotropy.frames_present(self.specimens)

    def frame_counts(self) -> dict:
        """Specimens the application can show in each frame — rows in the table plus what it can rotate."""
        return {key: len(self.tensors(key)) for key in anisotropy.COORDINATES}

    def index(self) -> pd.DataFrame:
        """One row per specimen with a tensor, whatever frame it is in (``anisotropy.specimen_index``)."""
        if "index" not in self._tensors:
            self._tensors["index"] = anisotropy.specimen_index(self.specimens)
        return self._tensors["index"]

    def n_specimens(self) -> int:
        return len(self.index())

    def types(self) -> list:
        """The anisotropy types present (AMS, AARM, ...), in the table's order."""
        index = self.index()
        return [str(v) for v in index["aniso_type"].dropna().unique()] if len(index) else []

    def groups(self, level: Optional[str] = None) -> list:
        """The group names at a level, in natural order, ``ALL`` first."""
        level = level or self.level
        index = self.index()
        if not len(index) or level not in index.columns:
            return [ALL]
        names = sorted(index[level].dropna().astype(str).unique(), key=natural_key)
        return [ALL] + names

    def selection(self) -> pd.DataFrame:
        """The tensors of the selected group, type and frame — what every view shows."""
        t = self.tensors(self.coordinates)
        if not len(t):
            return t
        if self.group != ALL:
            t = t[t[self.level].astype(str) == self.group]
        if self.aniso_type:
            t = t[t["aniso_type"].astype(str) == self.aniso_type]
        return t.reset_index(drop=True)

    def selection_label(self) -> str:
        """A short name for the selection: ``mc121 · AARM · geographic``."""
        parts = [self.group if self.group != ALL else ALL]
        if self.aniso_type:
            parts.append(self.aniso_type)
        parts.append(anisotropy.COORDINATE_NAMES[self.coordinates])
        return " · ".join(parts)


def as_session(data) -> Session:
    """A :class:`Session` from what a view was given: a session, a specimens DataFrame, or a directory path."""
    if isinstance(data, Session):
        return data
    if isinstance(data, pd.DataFrame):
        return Session(specimens=data)
    return Session(str(data))

"""
The session: the measurements of one MagIC directory, the experiment index
built from them, and the state the views share.

Rock-magnetic analysis in ``pmagpy.rockmag`` is a family of pure functions
over the measurements DataFrame, so the session is thin: it reads the
directory (through ``MagicProject``, like the other applications), groups the
experiments by type from their method codes, and remembers which specimen is
being looked at. A session can also be made from a DataFrame that is already
in memory — that is how the views render inside a notebook.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import param

from pmagpy.magic_project import MagicProject, natural_key
from pmagpy_panel import AppInfo, datasets

APP = AppInfo(name="PmagPy Rock Magnetism", app_id="pmagpy_rockmag", env_prefixes=("PMAGPY_ROCKMAG_",))


def env(name: str, default: str = "") -> str:
    """Environment setting ``PMAGPY_ROCKMAG_<name>``."""
    return datasets.env(name, APP.env_prefixes, default)


RECENT_FILE = env("RECENT", datasets.shared_recent_file())


def session_directory(default: str) -> str:
    """The directory this session opens: ``?dir=`` on the URL, then ``PMAGPY_ROCKMAG_DIR``, then `default`."""
    return datasets.session_directory(APP.env_prefixes, default)


# ----------------------------------------------------------------------------- experiment types
@dataclass(frozen=True)
class ExperimentType:
    """One kind of rock-magnetic experiment, recognised by method codes.

    `codes` are matched as whole codes within a row's ``method_codes``
    (``LP-X-T`` matches ``LP-X:LP-X-T:LP-X-F``); a code ending in ``-`` is a
    prefix (``LP-CW-`` matches ``LP-CW-SIRM``).
    """
    key: str
    label: str
    codes: tuple

    def matches(self, method_codes: str) -> bool:
        parts = [c.strip() for c in str(method_codes or "").split(":")]
        for code in self.codes:
            if code.endswith("-"):
                if any(p.startswith(code) for p in parts):
                    return True
            elif code in parts:
                return True
        return False


MPMS_DC_CODES = ("LP-FC", "LP-ZFC", "LP-CW-SIRM")

# the views' order; each type is one view in the application
EXPERIMENT_TYPES = [
    ExperimentType("mpms_dc", "MPMS DC", MPMS_DC_CODES),
    ExperimentType("mpms_ac", "AC susceptibility", ("LP-X-F",)),
    ExperimentType("chi_t", "χ–T", ("LP-X-T",)),
    ExperimentType("ms_t", "Ms–T", ("LP-MST", "LP-IMT")),
    ExperimentType("hys", "Hysteresis", ("LP-HYS", "LP-HYS-")),
    ExperimentType("bcr", "Backfield", ("LP-BCR", "LP-BCR-")),
    ExperimentType("irm", "IRM acquisition", ("LP-IRM", "LP-IRM-")),
    ExperimentType("forc", "FORC", ("LP-FORC",)),
]
TYPES_BY_KEY = {t.key: t for t in EXPERIMENT_TYPES}


def experiment_index(measurements: Optional[pd.DataFrame]) -> pd.DataFrame:
    """The experiments in `measurements`, one row each, typed.

    Columns: ``specimen``, ``method_codes``, ``experiment``, ``n`` (rows) and
    ``type`` (an :data:`EXPERIMENT_TYPES` key, or "" when no view claims it).
    Empty when there are no measurements.
    """
    columns = ["specimen", "method_codes", "experiment", "n", "type"]
    if measurements is None or not len(measurements):
        return pd.DataFrame(columns=columns)
    needed = ["specimen", "method_codes", "experiment"]
    m = measurements.reindex(columns=needed).fillna("")
    index = m.groupby(needed, sort=False).size().reset_index(name="n")

    def kind(codes):
        for t in EXPERIMENT_TYPES:
            if t.matches(codes):
                return t.key
        return ""
    index["type"] = index["method_codes"].map(kind)
    index = index.sort_values("specimen", key=lambda s: s.map(natural_key), kind="stable")
    return index.reset_index(drop=True)[columns]


# ----------------------------------------------------------------------------- session
class Session(param.Parameterized):
    """State shared by the views; views watch ``directory`` and ``specimen``."""

    directory = param.String(default="", doc="MagIC directory that was loaded ('' for in-memory data)")
    specimen = param.String(default="", doc="the specimen being looked at")
    status = param.String(default="")

    def __init__(self, directory: Optional[str] = None, measurements: Optional[pd.DataFrame] = None, **params):
        super().__init__(**params)
        self.project: Optional[MagicProject] = None
        self.measurements: Optional[pd.DataFrame] = None
        self.experiments: pd.DataFrame = experiment_index(None)
        if measurements is not None:
            self.set_measurements(measurements, status=f"{len(measurements)} measurements in memory")
        elif directory:
            self.load(directory)

    # ------------------------------------------------------------------ loading
    def load(self, directory: str) -> bool:
        """Read `directory`; False (with ``status`` saying why) when it cannot be read."""
        directory = os.path.abspath(os.path.expanduser(directory))
        if not datasets.looks_like_magic_dir(directory):
            self.status = f"{directory} has no measurements.txt"
            return False
        try:
            project = MagicProject.from_directory(directory, app_id=APP.app_id)
            measurements = project.table("measurements")
        except Exception as ex:                                            # a malformed table is reported, not raised
            self.status = f"could not read {directory}: {ex}"
            return False
        if measurements is None:
            self.status = f"{directory}: measurements.txt is empty"
            return False
        self.project = project
        self.set_measurements(measurements, status="")
        n_types = len(self.type_counts())
        self.status = (f"{self.experiments['specimen'].nunique()} specimens · {len(self.experiments)} experiments"
                       f" · {n_types} experiment type{'s' if n_types != 1 else ''}")
        self.directory = directory
        return True

    def set_measurements(self, measurements: pd.DataFrame, status: str = "") -> None:
        """Take a measurements DataFrame as the session's data (a notebook's, or a directory's)."""
        self.measurements = measurements.reset_index(drop=True)
        self.experiments = experiment_index(self.measurements)
        specimens = self.specimens()
        if self.specimen not in specimens:
            self.specimen = specimens[0] if specimens else ""
        if status:
            self.status = status

    # ------------------------------------------------------------------ the index
    def experiments_of(self, type_key: str) -> pd.DataFrame:
        """The experiments of one type (an :data:`EXPERIMENT_TYPES` key)."""
        return self.experiments[self.experiments["type"] == type_key]

    def specimens(self, type_key: Optional[str] = None) -> list:
        """Specimen names in natural order — all of them, or those with an experiment of one type."""
        exps = self.experiments if type_key is None else self.experiments_of(type_key)
        return list(dict.fromkeys(exps["specimen"]))

    def type_counts(self) -> list:
        """``(ExperimentType, n_specimens, n_experiments)`` for every type present, in view order."""
        counts = []
        for t in EXPERIMENT_TYPES:
            exps = self.experiments_of(t.key)
            if len(exps):
                counts.append((t, exps["specimen"].nunique(), len(exps)))
        return counts

    def unclaimed(self) -> pd.DataFrame:
        """Experiments no view plots (paleomagnetic ones in a mixed contribution, or codes not yet handled)."""
        return self.experiments_of("")


def as_session(data) -> Session:
    """A :class:`Session` from what a view was given: a session, a DataFrame, or a directory path."""
    if isinstance(data, Session):
        return data
    if isinstance(data, pd.DataFrame):
        return Session(measurements=data)
    return Session(str(data))

"""
Finding, choosing and remembering a MagIC directory.

None of this knows what an application does with the data once it has it, so
every application shares it. Every function takes what it needs as an argument —
the environment prefixes to answer to, the file to keep the recent list in —
rather than reading a module-level configuration, so that several applications
can live in one process without one deciding where the other looks.

The system folder dialog itself is platform knowledge and lives in
:mod:`pmagpy_panel.runtime`; it is re-exported here for the callers that
learned it under this name.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional, Sequence

from .runtime import native_choose_directory, native_chooser_available, query_param  # noqa: F401

SHARED_RECENT_FILE = os.path.join(os.path.expanduser("~"), ".pmagpy", "recent_magic_dirs.json")


def env(name: str, prefixes: Sequence[str], default: str = "") -> str:
    """Environment setting ``<prefix><name>``, taking the first prefix that is set."""
    for prefix in prefixes:
        value = os.environ.get(prefix + name)
        if value:
            return value
    return default


def session_directory(prefixes: Sequence[str], default: str) -> str:
    """The MagIC directory this session should open.

    In order: ``?dir=`` on the URL that opened the session (so the hub, a
    bookmark or a script can point one browser tab at one dataset), then the
    ``<prefix>DIR`` environment setting the launcher writes, then `default`.
    """
    chosen = query_param("dir") or env("DIR", prefixes)
    return os.path.abspath(os.path.expanduser(chosen)) if chosen else default


def looks_like_magic_dir(directory: str) -> bool:
    """A directory a contribution could be read from: it has a measurements table."""
    return os.path.isdir(directory) and os.path.exists(os.path.join(directory, "measurements.txt"))


def default_output_dir(directory: str, base: str = "") -> str:
    """The data directory itself, or a folder of its own under ``base`` when a base is given.

    The folder is named after the dataset *and* a short fingerprint of its full
    path (``MagIC-3f2a91c0``): studies are often kept in folders with the same
    name (``MagIC``, ``data``), and two of them sharing one output folder would
    share -- and overwrite -- one autosave and one set of exported tables.
    """
    if base:
        import hashlib
        path = os.path.realpath(os.path.abspath(os.path.expanduser(directory)).rstrip("/"))
        tag = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
        return os.path.join(base, f"{os.path.basename(path)}-{tag}")
    return directory


#: the settings that name the one folder under which every application works on a copy of each
#: study (the shared one first; an application's own older setting still counts, for all of them)
OUTPUT_BASE_VARS = ("PMAGPY_APPS_OUTPUT", "PMAGPY_DIRECTIONS_OUTPUT", "PMAGPY_INTENSITY_OUTPUT",
                    "DEMAG_OUTPUT", "THELLIER_OUTPUT")
#: written into a working copy: where it was copied from, and when
WORKING_COPY_MARKER = ".pmagpy_working_copy.json"
#: the files of a study a working copy takes (MagIC tables, legacy .redo files, session files)
WORKING_COPY_SUFFIXES = (".txt", ".redo", ".json")


def output_base() -> str:
    """The folder the applications keep their working copies in, or "" to work in the study itself.

    Every application answers the same setting, so that PmagPy Directions,
    PmagPy Intensity, Rock Magnetism, Anisotropy and the hub all read and
    write one copy of a study rather than each keeping its own.
    """
    for var in OUTPUT_BASE_VARS:
        value = os.environ.get(var)
        if value:
            return os.path.abspath(os.path.expanduser(value))
    return ""


def is_working_copy(directory: str, base: str = "") -> bool:
    """True for a directory that is itself a working copy (inside ``base``, or marked as one)."""
    path = os.path.realpath(directory)
    if base and (path + os.sep).startswith(os.path.realpath(base) + os.sep):
        return True
    return os.path.isfile(os.path.join(path, WORKING_COPY_MARKER))


def working_copy_source(directory: str) -> str:
    """The study a working copy was made from ("" when it is not one, or does not say)."""
    try:
        with open(os.path.join(directory, WORKING_COPY_MARKER), encoding="utf-8") as fh:
            return str(json.load(fh).get("source", ""))
    except (OSError, ValueError, AttributeError):
        return ""


def working_directory(directory: str, base: Optional[str] = None) -> str:
    """The directory an application reads and writes for a study: its working copy when there is a base.

    With no base (a checkout, a pip install) that is the study itself, as it
    always was. With one (the desktop build sets ``~/PmagPy``; the setting is
    :func:`output_base`), the study's tables are copied once to
    ``<base>/<name>-<path fingerprint>/`` (:func:`default_output_dir`) and every
    application works there, so they all see one set of tables -- and the
    study itself is never written to. A copy that already exists is used as it
    is; files the study has gained since are added to it, files it has are
    never overwritten. Two applications opening the same study at once make
    one copy: it is assembled beside the target and moved into place whole.

    Raises:
        OSError: the copy cannot be made (the base is not writable, the disk is full).
    """
    directory = os.path.abspath(os.path.expanduser(directory))
    base = output_base() if base is None else base
    if not base or is_working_copy(directory, base):
        return directory
    target = default_output_dir(directory, base)
    files = [n for n in sorted(os.listdir(directory))
             if n.endswith(WORKING_COPY_SUFFIXES) and not n.startswith(".")
             and os.path.isfile(os.path.join(directory, n))]
    if os.path.isdir(target):
        import shutil
        for name in files:
            if not os.path.exists(os.path.join(target, name)):
                shutil.copy2(os.path.join(directory, name), os.path.join(target, name))
        if not os.path.exists(os.path.join(target, WORKING_COPY_MARKER)):
            _write_marker(target, directory)
        return target
    import shutil
    import tempfile
    os.makedirs(base, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".copying-", dir=base)
    try:
        for name in files:
            shutil.copy2(os.path.join(directory, name), os.path.join(staging, name))
        _write_marker(staging, directory)
        try:
            os.rename(staging, target)
        except OSError:
            if not os.path.isdir(target):          # not another application's copy landing first
                raise
    finally:
        if os.path.isdir(staging):
            shutil.rmtree(staging, ignore_errors=True)
    return target


def _write_marker(target: str, source: str) -> None:
    import time
    from pmagpy.magic_project import atomic_write_text
    atomic_write_text(os.path.join(target, WORKING_COPY_MARKER),
                      json.dumps({"source": os.path.realpath(source),
                                  "copied": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))


#: the tables whose files decide whether a dataset read earlier is still current
STAMPED_TABLES = ("measurements.txt", "specimens.txt", "samples.txt", "sites.txt", "locations.txt",
                  "criteria.txt", "ages.txt")


def table_stamp(directory: str, names: Sequence[str] = STAMPED_TABLES) -> tuple:
    """(name, size, modification time) of each table file: changes whenever a table is edited on disk."""
    stamp = []
    for name in names:
        try:
            st = os.stat(os.path.join(directory, name))
        except OSError:
            continue
        stamp.append((name, st.st_size, st.st_mtime_ns))
    return tuple(stamp)


def set_aside(path: str) -> str:
    """Rename a file that could not be read to ``<name>.unreadable-<time>`` beside it; returns the new path.

    Used for an autosave that no longer parses: it must not block opening the
    dataset, and it must not be silently overwritten by the next autosave
    either, in case it is worth recovering by hand.
    """
    import time
    target = f"{path}.unreadable-{time.strftime('%Y%m%d-%H%M%S')}"
    try:
        os.replace(path, target)
    except OSError:
        return path
    return target


def load_recent(path: str) -> list:
    """Recently opened MagIC directories (most recent first) that still exist."""
    try:
        with open(path, encoding="utf-8") as fh:
            return [d for d in json.load(fh) if isinstance(d, str) and os.path.isdir(d)]
    except (OSError, ValueError, TypeError):
        return []


def remember_recent(path: str, directory: str, limit: int = 12) -> list:
    """Put `directory` at the head of the recent list and write it back."""
    directory = os.path.abspath(directory)
    recent = [d for d in load_recent(path) if d != directory]
    recent.insert(0, directory)
    recent = recent[:limit]
    try:
        from pmagpy.magic_project import atomic_write_text
        atomic_write_text(path, json.dumps(recent, indent=1))
    except OSError:
        pass
    return recent


def shared_recent_file(migrate_from: Sequence[str] = ()) -> str:
    """The recent list every application shares, ``~/.pmagpy/recent_magic_dirs.json``.

    A directory opened in one application is then already in the others' lists.
    The first time it is asked for, the list is seeded from the per-application
    files earlier builds kept (`migrate_from`, most recent first), which are left
    in place.
    """
    path = SHARED_RECENT_FILE
    if os.path.exists(path):
        return path
    seeds = [d for old in migrate_from for d in load_recent(old)]
    if not seeds:
        return path
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(list(dict.fromkeys(seeds)), fh, indent=1)
    except OSError:
        pass
    return path


def example_dir(name: str) -> str:
    """The MagIC example dataset ``data_files/3_0/<name>`` that ships with PmagPy.

    Found beside the code in a checkout (which is also what an editable install
    is), or under ``sys.prefix`` where a wheel install puts ``data_files``. Empty
    when neither has it.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    for base in (os.path.join(repo, "data_files"), os.path.join(sys.prefix, "data_files")):
        candidate = os.path.join(base, "3_0", name)
        if looks_like_magic_dir(candidate):
            return candidate
    return ""

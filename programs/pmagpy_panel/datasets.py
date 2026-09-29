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
from typing import Sequence

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

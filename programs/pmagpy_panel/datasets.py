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

    An example dataset that ships with PmagPy (:func:`is_bundled_example`) is
    keyed by its name instead (``McMurdo-example``): its path changes whenever
    the application is moved, updated or run translocated, and the work done
    on the example should not be left behind each time.
    """
    if base:
        import hashlib
        path = os.path.realpath(os.path.abspath(os.path.expanduser(directory)).rstrip("/"))
        if is_bundled_example(path):
            return os.path.join(base, f"{os.path.basename(path)}-example")
        tag = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
        # a folder name is at most 255 bytes: a long study name is shortened (the fingerprint keeps it unique)
        name = os.path.basename(path).encode("utf-8")[:200].decode("utf-8", "ignore")
        return os.path.join(base, f"{name}-{tag}")
    return directory


#: the settings that name the PmagPy folder (the shared one first; an application's own older
#: setting still counts, for all of them); unset, it is :data:`DEFAULT_HOME`
OUTPUT_BASE_VARS = ("PMAGPY_APPS_OUTPUT", "PMAGPY_DIRECTIONS_OUTPUT", "PMAGPY_INTENSITY_OUTPUT",
                    "DEMAG_OUTPUT", "THELLIER_OUTPUT")
#: written into a working copy: where it was copied from, and when
WORKING_COPY_MARKER = ".pmagpy_working_copy.json"
#: the files of a study a working copy takes (MagIC tables, legacy .redo files, session files)
WORKING_COPY_SUFFIXES = (".txt", ".redo", ".json")
#: the log PmagPy writes beside the tables it converted (``pmagpy.convert_registry.CONVERSION_LOG``):
#: a study that has one is PmagPy's own work, and is worked on in place
CONVERSION_LOG = "pmagpy_conversions.json"
#: the table MagIC serves with every contribution, and no converter writes
CONTRIBUTION_TABLE = "contribution.txt"


#: the PmagPy folder when no setting names another: copies of the examples, contributions downloaded from MagIC
DEFAULT_HOME = os.path.join("~", "PmagPy")


def output_base() -> str:
    """The PmagPy folder: where the examples are copied to and contributions from MagIC are downloaded.

    ``PMAGPY_APPS_OUTPUT`` (``pmagpy-apps --output``, or an application's own
    older setting) names it; unset, it is ``~/PmagPy``. A study the analyst
    opens is worked on where it is (:func:`working_directory`); this folder
    only takes what cannot be: the datasets that ship with PmagPy, and a
    study in a folder that cannot be written.
    """
    for var in OUTPUT_BASE_VARS:
        value = os.environ.get(var)
        if value:
            return os.path.abspath(os.path.expanduser(value))
    return os.path.abspath(os.path.expanduser(DEFAULT_HOME))


def is_working_copy(directory: str, base: str = "") -> bool:
    """True for a directory that is itself a working copy: one that holds :data:`WORKING_COPY_MARKER`.

    Where it is does not count (``base`` is accepted for the callers that pass
    it): a study the analyst keeps under the output base gets a copy of its own
    like any other.
    """
    return os.path.isfile(os.path.join(os.path.realpath(directory), WORKING_COPY_MARKER))


def shipped_roots() -> list:
    """The folders that come with PmagPy itself: the packaged application, and the ``data_files`` of a
    checkout or an install. Nothing under them is ever worked on in place."""
    roots = []
    if getattr(sys, "frozen", False):
        roots.append(getattr(sys, "_MEIPASS", ""))
        executable = os.path.realpath(sys.executable)
        bundle = executable
        while bundle != os.path.dirname(bundle) and not bundle.endswith(".app"):
            bundle = os.path.dirname(bundle)
        roots.append(bundle if bundle.endswith(".app") else os.path.dirname(executable))
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    roots += [os.path.join(repo, "data_files"), os.path.join(sys.prefix, "data_files")]
    return [os.path.realpath(r) for r in roots if r]


def _under(path: str, roots) -> bool:
    return any(path == root or path.startswith(root + os.sep) for root in roots)


def is_bundled_example(directory: str) -> bool:
    """True for an example dataset that ships with PmagPy: ``data_files/3_0/<name>`` of the packaged
    application, an install or a checkout -- where :func:`example_dir` finds it, or anywhere under
    :func:`shipped_roots` laid out that way."""
    path = os.path.realpath(os.path.abspath(os.path.expanduser(directory)).rstrip(os.sep))
    name = os.path.basename(path)
    if not name or not os.path.isdir(path):
        return False
    found = example_dir(name)
    if found and os.path.realpath(found) == path:
        return True
    parent = os.path.dirname(path)
    return (os.path.basename(parent) == "3_0" and os.path.basename(os.path.dirname(parent)) == "data_files"
            and _under(path, shipped_roots()))


def needs_copy(directory: str) -> bool:
    """True for a study that is not worked on where it is, but in a working copy in the PmagPy folder.

    That is a dataset that ships with PmagPy (an example in the application or
    a checkout's ``data_files``, :func:`shipped_roots`), or one in a folder
    that cannot be written (a read-only share). A table its owner made
    read-only in a writable study does not count: the study is worked on in
    place and that table is left as it is (an export says so).
    Every other study -- the analyst's own folder, a git repository, a
    contribution downloaded from MagIC -- is read and written in place: its
    lab files are never edited, and its MagIC tables, session files and
    exports are where the analyst keeps (and versions) the study.
    """
    path = os.path.realpath(os.path.abspath(os.path.expanduser(directory)))
    if _under(path, shipped_roots()) or is_bundled_example(path):
        return True
    return not os.access(path, os.W_OK)


def _conversions(directory: str) -> list:
    """The entries of a folder's :data:`CONVERSION_LOG`, oldest first (empty when there is none)."""
    try:
        with open(os.path.join(directory, CONVERSION_LOG), encoding="utf-8") as fh:
            entries = json.load(fh)
    except (OSError, ValueError):
        return []
    return [e for e in entries if isinstance(e, dict)] if isinstance(entries, list) else []


def _since_last_replace(entries: list) -> list:
    """The log entries that account for the tables as they stand: the last one that replaced them and
    every append since (as ``pmagpy.convert_registry.conversion_sources``)."""
    kept: list = []
    for entry in entries:
        if not entry.get("append"):
            kept = []
        kept.append(entry)
    return kept


def from_magic(directory: str) -> bool:
    """True for a folder whose tables came from MagIC: a published contribution, someone's record.

    That is a contribution file unpacked on the Convert page or a contribution
    downloaded by the hub (its log entry has format ``magic``, among those that
    account for the tables), or a folder holding :data:`CONTRIBUTION_TABLE`
    whose tables were there before any conversion PmagPy logged replaced them --
    a contribution downloaded from the website, or by a build that did not log
    downloads -- with or without lab files added to it since. Such a folder is
    worked on in a working copy, never in place.
    """
    entries = _conversions(directory)
    if any(e.get("format") == "magic" for e in _since_last_replace(entries)):
        return True
    return os.path.isfile(os.path.join(directory, CONTRIBUTION_TABLE)) and all(e.get("append") for e in entries)


def _marked_source(directory: str) -> str:
    """The study a working copy's marker names, whether or not it is still there."""
    try:
        with open(os.path.join(directory, WORKING_COPY_MARKER), encoding="utf-8") as fh:
            return str(json.load(fh).get("source", ""))
    except (OSError, ValueError, AttributeError):
        return ""


def working_copy_source(directory: str) -> str:
    """The study a working copy was made from ("" when it is not one, does not say, or that study is gone).

    A copy moved to another folder or computer, or one whose study was moved
    or renamed since, names a folder that is not there: the copy is then its
    own study, shown and remembered under its own path
    (:func:`working_copy_note` says why).
    """
    source = _marked_source(directory)
    return source if source and os.path.isdir(source) else ""


def working_copy_note(directory: str) -> str:
    """A sentence for a working copy whose study is not where its marker says, else ""."""
    source = _marked_source(directory)
    if not source or os.path.isdir(source):
        return ""
    return (f"This working copy was made from {source}, which is not there any more; "
            "it is opened as a study of its own.")


def study_name(directory: str) -> str:
    """The name to show for a study: its folder's name, also when `directory` is its working copy.

    A working copy's own folder carries a path fingerprint (``McMurdo-1a2b3c4d``),
    which means nothing to the analyst; the study it was made from is ``McMurdo``,
    also when that folder has since moved.
    """
    path = _marked_source(directory) or directory
    return os.path.basename(os.path.abspath(path).rstrip(os.sep)) or path


def shorten_home(path: str) -> str:
    """`path` with the home folder written as ``~``."""
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path == home or path.startswith(home + os.sep) else path


def working_directory(directory: str, base: Optional[str] = None) -> str:
    """The directory an application reads and writes for a study: the study itself, unless it needs a copy.

    A study is worked on where the analyst keeps it -- the folder chosen in
    Open MagIC data or converted into on the Convert page -- so that its
    tables, session files and exports stay with it (in its git repository,
    say). Only a study that cannot be (:func:`needs_copy`: one that ships with
    PmagPy, or a read-only one) is copied, once, to
    ``<PmagPy folder>/<name>-<path fingerprint>/`` (:func:`default_output_dir`;
    an example to ``<name>-example``), and every application works there. A
    copy that already exists is used as it is; files the study has gained
    since are added to it, files it has are never overwritten. Two
    applications opening the same study at once make one copy: it is
    assembled beside the target and moved into place whole.

    A working copy opened itself is worked on as it is. A study that an
    earlier build copied (it worked on every study in a copy) is worked on in
    place all the same; the work in that copy is offered to it
    (:func:`earlier_copy`, :func:`bring_over`).

    Raises:
        OSError: a copy is needed and cannot be made (the PmagPy folder is not writable, the disk is full).
    """
    directory = os.path.abspath(os.path.expanduser(directory))
    if is_working_copy(directory) or not needs_copy(directory):
        return directory
    base = base or output_base()
    target = default_output_dir(directory, base)
    files = [n for n in sorted(os.listdir(directory))
             if n.endswith(WORKING_COPY_SUFFIXES) and not n.startswith(".")
             and os.path.isfile(os.path.join(directory, n))]
    if os.path.isdir(target):
        added = {}
        for name in files:
            if not os.path.exists(os.path.join(target, name)):
                added[name] = _file_stamp(os.path.join(directory, name))
                _copy_writable(os.path.join(directory, name), os.path.join(target, name))
        marker = _read_marker(target)
        if not marker or added or (is_bundled_example(directory) and _marked_source(target) != os.path.realpath(directory)):
            # the example's copy follows the application it came with
            _write_marker(target, directory, added)
        return target
    import shutil
    import uuid
    os.makedirs(base, exist_ok=True)
    staging = os.path.join(base, f".copying-{uuid.uuid4().hex[:12]}")
    os.mkdir(staging, 0o777)
    try:
        stamps = {}
        for name in files:
            stamps[name] = _file_stamp(os.path.join(directory, name))
            _copy_writable(os.path.join(directory, name), os.path.join(staging, name))
        _write_marker(staging, directory, stamps, fresh=True)
        try:
            os.rename(staging, target)
        except OSError:
            if not os.path.isdir(target):          # not another application's copy landing first
                raise
    finally:
        if os.path.isdir(staging):
            shutil.rmtree(staging, ignore_errors=True)
    return target


def _copy_writable(src: str, dst: str) -> None:
    """Copy a study's file into its working copy, which the applications write: a read-only
    study (a download kept read-only, an archive, a read-only share) gives writable copies,
    so that no writer -- an atomic replace or a plain open() -- meets a read-only table there."""
    import shutil
    import stat
    shutil.copy2(src, dst)
    mode = os.stat(dst).st_mode
    if not mode & stat.S_IWUSR:
        os.chmod(dst, stat.S_IMODE(mode) | stat.S_IWUSR)


def _file_stamp(path: str) -> dict:
    """``{"size", "mtime_ns", "sha1"}`` of a study's file as it is copied (empty when it cannot be read)."""
    try:
        st = os.stat(path)
        return {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "sha1": _sha1(path)}
    except OSError:
        return {}


def _sha1(path: str) -> str:
    import hashlib
    digest = hashlib.sha1()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_marker(directory: str) -> dict:
    try:
        with open(os.path.join(directory, WORKING_COPY_MARKER), encoding="utf-8") as fh:
            marker = json.load(fh)
    except (OSError, ValueError):
        return {}
    return marker if isinstance(marker, dict) else {}


def _write_marker(target: str, source: str, stamps: Optional[dict] = None, fresh: bool = False) -> None:
    """Write the marker: the study, when the copy was made, the copy's id, and what each file copied from it was.

    ``files`` (name → size, modification time and checksum of the study's file
    when it was copied) is what :func:`copy_changes` compares the study with.
    A new copy records every file; an existing one adds the files copied now
    to its record -- but a marker that never had one (a copy made before
    copies recorded their files) stays without, so that it reads as unknown.
    ``id`` is new with every copy and kept for its life (:func:`copy_id`).
    """
    import time
    import uuid
    from pmagpy.magic_project import atomic_write_text
    old = {} if fresh else _read_marker(target)
    marker = {"source": os.path.realpath(source),
              "copied": old.get("copied") or time.strftime("%Y-%m-%dT%H:%M:%S")}
    if fresh:
        marker["id"] = uuid.uuid4().hex
    elif old.get("id"):
        marker["id"] = old["id"]
    if fresh:
        marker["files"] = dict(stamps or {})
    elif isinstance(old.get("files"), dict):
        marker["files"] = {**old["files"], **(stamps or {})}
    atomic_write_text(os.path.join(target, WORKING_COPY_MARKER), json.dumps(marker, indent=1))


def copy_id(directory: str) -> Optional[str]:
    """Which working copy is at ``directory`` now: its marker's ``id`` ("" for a copy made before copies had
    one), or None when no working copy is there (a study worked on in place, or a copy set aside).

    A window that opened the copy remembers it (:class:`pmagpy_panel.autosave.AutosaveGuard`): after
    "Start a fresh copy" another copy is at the same path, and a window still open on the old one
    must not write its autosave or an export into the new one.
    """
    path = os.path.join(directory, WORKING_COPY_MARKER)
    if not os.path.isfile(path):
        return None
    return str(_read_marker(directory).get("id", ""))


def copy_changes(directory: str) -> Optional[list]:
    """The study's files that have changed since this working copy was made from it, by name (sorted).

    None when that cannot be told: `directory` is not a copy, its study is not
    there, or the copy was made before copies recorded their files. A file
    counts as changed when it is gone, its size differs, or its modification
    time differs and so does its checksum (a study moved or unpacked again
    keeps its contents and loses its times).
    """
    recorded = _read_marker(directory).get("files")
    source = working_copy_source(directory)
    if not source or not isinstance(recorded, dict) or os.path.realpath(source) == os.path.realpath(directory):
        return None
    changed = []
    for name, stamp in recorded.items():
        path = os.path.join(source, name)
        try:
            st = os.stat(path)
            if st.st_size != stamp.get("size") or (st.st_mtime_ns != stamp.get("mtime_ns")
                                                   and _sha1(path) != stamp.get("sha1")):
                changed.append(name)
        except OSError:
            changed.append(name)
    return sorted(changed)


def stale_copy_note(directory: str) -> str:
    """A sentence for a working copy whose study has changed since it was made, else ""."""
    changed = copy_changes(directory)
    if not changed:
        return ""
    names = ", ".join(changed[:4]) + (f" and {len(changed) - 4} more" if len(changed) > 4 else "")
    when = str(_read_marker(directory).get("copied", ""))[:10]
    return (f"The study has changed since this working copy was made{' on ' + when if when else ''} ({names}): "
            "the applications show it as it was then.")


def can_start_fresh(directory: str) -> bool:
    """True for the working copy its study's applications open (not one set aside by :func:`set_copy_aside`)."""
    source = working_copy_source(directory)
    if not source:
        return False
    return os.path.realpath(default_output_dir(source, os.path.dirname(os.path.realpath(directory)))) == \
        os.path.realpath(directory)


def set_copy_aside(directory: str, today=None) -> str:
    """Rename a working copy to ``<its name>-<YYYY-MM-DD>`` (``-2``, ``-3`` … when taken) and return its study.

    Its tables, interpretations and session files are kept as they are, never
    overwritten; opening the study next makes a new copy from it, or, for a
    study that is worked on in place, opens it there (:func:`working_directory`).

    Raises:
        OSError: the copy's study is not there, or the copy cannot be renamed.
    """
    from datetime import date
    source = working_copy_source(directory)
    if not source:
        raise OSError(f"{directory} is not a working copy of a study that is there")
    path = os.path.realpath(directory)
    stem = f"{path}-{(today or date.today()).isoformat()}"
    aside, n = stem, 1
    while os.path.lexists(aside):
        n += 1
        aside = f"{stem}-{n}"
    os.rename(path, aside)
    return source


def is_superseded_copy(directory: str) -> bool:
    """True for a working copy whose study is there and is now worked on in place (an earlier build
    copied every study): the applications use the study, and this copy's work can be brought to it."""
    source = working_copy_source(directory)
    return (bool(source) and os.path.realpath(source) != os.path.realpath(directory)
            and not needs_copy(source))


def copy_remedy(directory: str) -> str:
    """What Home offers for a working copy that lacks tables written into its study since."""
    return ("Home offers to bring the copy's work into the study" if is_superseded_copy(directory)
            else "Home offers to start afresh")


def earlier_copy(directory: str) -> str:
    """The working copy of the study at ``directory`` whose work is not in the study yet, or "".

    For a study worked on in place, the copy an earlier build made of it in the
    PmagPy folder (still at its own path, not set aside); for such a copy
    opened itself, the copy.
    """
    if not directory or not os.path.isdir(directory):
        return ""
    if is_working_copy(directory):
        return os.path.realpath(directory) if is_superseded_copy(directory) else ""
    if needs_copy(directory):
        return ""
    copy = default_output_dir(directory, output_base())
    if os.path.isdir(copy) and is_working_copy(copy) and \
            os.path.realpath(_marked_source(copy) or "") == os.path.realpath(directory):
        return os.path.realpath(copy)
    return ""


def _work_in(copy: str) -> list:
    """The files of a working copy that differ from its study's (or that the study lacks), by name."""
    source = working_copy_source(copy)
    names = []
    for name in sorted(os.listdir(copy)):
        path = os.path.join(copy, name)
        if name.startswith(".") or not name.endswith(WORKING_COPY_SUFFIXES) or not os.path.isfile(path):
            continue
        theirs = os.path.join(source, name)
        if not os.path.isfile(theirs) or _sha1(theirs) != _sha1(path):
            names.append(name)
    return names


def earlier_copy_note(directory: str) -> str:
    """A sentence for a study with an earlier working copy (or for that copy), else ""."""
    copy = earlier_copy(directory)
    if not copy:
        return ""
    source = working_copy_source(copy)
    when = str(_read_marker(copy).get("copied", ""))[:10]
    work = _work_in(copy)
    if os.path.realpath(directory) == copy:
        where = (f"This is a working copy an earlier PmagPy made{' on ' + when if when else ''}; the applications "
                 f"now work in the study itself, {shorten_home(source)}.")
    else:
        where = (f"An earlier PmagPy worked on this study in a copy, {shorten_home(copy)}"
                 f"{' (made ' + when + ')' if when else ''}.")
    if not work:
        return where + " It holds nothing the study does not."
    names = ", ".join(work[:4]) + (f" and {len(work) - 4} more" if len(work) > 4 else "")
    note = (where + f" Its {names} differ from the study's: bring them into the study to carry on with that work "
            "(the study's own are backed up first).")
    changed = [name for name in (copy_changes(copy) or []) if name in work]
    if changed:
        note += (f" The study's {', '.join(changed[:4])} changed after the copy was made: bringing the copy's "
                 "over replaces those changes, which stay in the backup.")
    return note


#: the folder in a study that keeps its own files that :func:`bring_over` replaced
BROUGHT_OVER_BACKUP = "backup_before_working_copy"


def bring_over(copy: str, today=None) -> tuple:
    """Bring an earlier working copy's work into its study, then set the copy aside.

    Every file of the copy that the study lacks or has otherwise (its MagIC
    tables, session files, ``.redo`` files) is copied into the study; a study
    file it replaces is first kept in ``<study>/backup_before_working_copy-<date>/``.
    The copy is then renamed with the date (:func:`set_copy_aside`), so it is
    not offered again and a window still open on it writes nothing more.

    Returns:
        (the study, the names of the files brought over).

    Raises:
        OSError: the copy's study is not there, or a file cannot be written.
    """
    import shutil
    from datetime import date
    source = working_copy_source(copy)
    if not source:
        raise OSError(f"{copy} is not a working copy of a study that is there")
    names = _work_in(copy)
    if names:
        stem = os.path.join(source, f"{BROUGHT_OVER_BACKUP}-{(today or date.today()).isoformat()}")
        backup, n = stem, 1
        while os.path.lexists(backup):
            n += 1
            backup = f"{stem}-{n}"
        for name in names:
            theirs = os.path.join(source, name)
            if os.path.isfile(theirs):
                os.makedirs(backup, exist_ok=True)
                shutil.copy2(theirs, os.path.join(backup, name))
        for name in names:
            staged = os.path.join(source, f".{name}.bringing-over")
            shutil.copy2(os.path.join(copy, name), staged)
            os.replace(staged, os.path.join(source, name))
    set_copy_aside(copy, today)
    return source, names


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

"""
Autosaves that two windows on one study do not overwrite.

PmagPy Directions and PmagPy Intensity write their work in progress to an
autosave beside the study, a moment after each edit. Two windows (browser
tabs, or two servers) holding two separate copies of one study would each
write their own copy over the other's, and whichever wrote last decided what
the next start restored. A dataset in memory therefore remembers the autosave
as it last read or wrote it -- its size and modification time -- and writes
its own name into the file; before writing again it checks that the file is
still that one. When another window has written it since, the autosave is
not written: the window says so and keeps its edits in memory, and an
explicit export still writes them.

Windows sharing one dataset (tabs opened on a study already open in the
server) share its guard, as they share its edits, and do not count as
another window.

The guard also remembers which working copy the autosave's folder was when
the dataset was read (:func:`pmagpy_panel.datasets.copy_id`). "Start a fresh
copy" sets that copy aside and makes a new one at the same path: a window
still open on the old copy then writes neither its autosave nor an export
(:meth:`AutosaveGuard.check`) into the new one, and says to reload.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Optional

from . import datasets

#: what the header says when another window has written the autosave since this one read it
ANOTHER_WINDOW = ("another window is editing this study — reload to see its changes (this window's edits are "
                  "not auto-saved; an export still writes them)")
#: what the header says when the working copy this window opened was set aside and a new one made in its place
COPY_REPLACED = ("this window's working copy was set aside and a new copy of the study made in its place "
                 "(Start a fresh copy) — reload to work on the new copy; this window writes nothing into it")


class WorkingCopyReplaced(OSError):
    """An export from a window whose working copy was set aside: it would write into the new copy."""


def file_stamp(path: str) -> Optional[tuple]:
    """``(modification time in ns, size)`` of a file, or None when there is none."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def writer_of(path: str) -> str:
    """The ``writer`` an autosave names ("" when it names none or cannot be read)."""
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return ""
    return str(payload.get("writer", "")) if isinstance(payload, dict) else ""


class AutosaveGuard:
    """What one dataset in memory knows of its autosave files.

    Attributes:
        writer: this dataset's name, written into each autosave it writes.
        seen: path -> the file's stamp (:func:`file_stamp`) when this dataset last read or wrote it.
        copies: folder -> the working copy it was (:func:`pmagpy_panel.datasets.copy_id`) when this
            dataset read its autosave there.
        refusal: why :meth:`may_write` last said no, for the header.
    """

    def __init__(self):
        self.writer = uuid.uuid4().hex
        self.seen: dict = {}
        self.copies: dict = {}
        self.refusal = ANOTHER_WINDOW

    def read(self, path: str) -> None:
        """The autosave at ``path`` is about to be read (or found absent): remember it, and its folder, as they are."""
        self.seen[os.path.abspath(path)] = file_stamp(path)
        folder = os.path.dirname(os.path.abspath(path))
        self.copies[folder] = datasets.copy_id(folder)

    def replaced(self, folder: str) -> bool:
        """True when the working copy at ``folder`` is not the one this dataset was read from."""
        folder = os.path.abspath(folder)
        return folder in self.copies and datasets.copy_id(folder) != self.copies[folder]

    def check(self, folder: str) -> None:
        """Before an export into ``folder``.

        Raises:
            WorkingCopyReplaced: the working copy there was set aside and a new one made since this dataset was read.
        """
        if self.replaced(folder):
            raise WorkingCopyReplaced(COPY_REPLACED)

    def wrote(self, path: str) -> None:
        self.seen[os.path.abspath(path)] = file_stamp(path)

    def may_write(self, path: str) -> bool:
        """False when another window has written the autosave at ``path`` since this dataset read or wrote it, or
        its folder is another working copy than the one this dataset was read from (:attr:`refusal` says which)."""
        path = os.path.abspath(path)
        if self.replaced(os.path.dirname(path)):
            self.refusal = COPY_REPLACED
            return False
        self.refusal = ANOTHER_WINDOW
        if path not in self.seen:
            return True
        now = file_stamp(path)
        if now is None or now == self.seen[path]:
            return True
        return writer_of(path) == self.writer


def refusal_of(data) -> str:
    """What the header says when a dataset's autosave is not written (:attr:`AutosaveGuard.refusal`)."""
    guard = getattr(data, "autosave_guard", None)
    return guard.refusal if guard is not None else ANOTHER_WINDOW


def guard_of(data) -> AutosaveGuard:
    """The guard a dataset carries (given one the first time it is asked for)."""
    guard = getattr(data, "autosave_guard", None)
    if guard is None:
        guard = AutosaveGuard()
        data.autosave_guard = guard
    return guard

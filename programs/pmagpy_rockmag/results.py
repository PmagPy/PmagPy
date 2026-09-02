"""
Results back into the specimens table.

Each analysis ends where the RockmagPy notebooks end: one of
``pmagpy.rockmag``'s ``add_*_to_specimens_table`` writers puts what was
measured on the specimen's row (or its component rows) of ``specimens.txt``.
:class:`SpecimenSave` is the toolkit's :class:`pmagpy_panel.results.TableSave`
for that table — the button under a view's result that runs the writer
through ``MagicProject`` (one backup, the software tag on the rows touched,
the calls appended to ``specimens.py`` beside the table). A specimen must
already have a row: the writers add results to rows, not rows to the table,
so a directory without ``specimens.txt`` is pointed to the Metadata page.
"""
from __future__ import annotations

import os

from pmagpy_panel import code
from pmagpy_panel.results import FAIL_COLOR, OK_COLOR, TableSave, changed_rows  # noqa: F401  (re-exported for tests)
from .session import APP, Session

TABLE = "specimens"
SCRIPT = "specimens.py"


def _missing(directory: str) -> str:
    return (f"no specimens.txt in {os.path.basename(directory)} — describe the specimens on the "
            "Metadata page first, then the results have a row to go to")


class SpecimenSave(TableSave):
    """The "Save to specimens.txt" step under a rock-magnetic view's result."""

    def __init__(self, session: Session, code_pane: code.CodePane, what: str):
        super().__init__(session, code_pane, what, table=TABLE, app=APP, label=lambda: session.specimen,
                         missing=_missing)

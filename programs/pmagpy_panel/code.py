"""
"Show code": the Python that reproduces what a view is showing.

Every analysis view in the family can say which core call it stands for — the
data it read, the specimen, the parameters the analyst set — as a few lines
an analyst can paste into a notebook (HUB_PLAN §3, "Every pathway documents
itself"). A view builds the text with :func:`call` and keeps it in a
:class:`CodePane`, which shows it on request; exports write the same text
beside the file they produce with :func:`write_beside`, so a figure or a
results table always comes with the lines that made it.

Nothing here knows about any particular science; the views supply the names.
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

import numpy as np
import panel as pn

from .theme import MUTED_STYLE

HEADER = "# written by {app} — the calls that made {what}"


def literal(value) -> str:
    """`value` as Python source: numbers plainly, strings quoted, sequences as tuples/lists.

    Floats are shortened to what repr needs (``0.1``, not ``0.10000000000000001``);
    numpy scalars become plain Python ones. A :class:`Name` is written as it is,
    for a variable the preamble has already bound.
    """
    if isinstance(value, Name):
        return str(value)
    if isinstance(value, bool) or value is None:
        return repr(value)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return repr(round(value, 10))
    if isinstance(value, (int, str)):
        return repr(value)
    if isinstance(value, tuple):
        inner = ", ".join(literal(v) for v in value)
        return f"({inner},)" if len(value) == 1 else f"({inner})"
    if isinstance(value, (list, np.ndarray)):
        return "[" + ", ".join(literal(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{literal(k)}: {literal(v)}" for k, v in value.items()) + "}"
    return repr(value)


class Name(str):
    """A variable name to write as-is in a call, e.g. ``Name("measurements")``."""


def call(func: str, *args, width: int = 88, **kwargs) -> str:
    """One call as source, e.g. ``call("rockmag.f", Name("df"), "sp1", deg=3)`` → ``rockmag.f(df, 'sp1', deg=3)``.

    Wraps one argument per line when the call would run past `width`.
    Keyword arguments keep the order given.
    """
    parts = [literal(a) for a in args] + [f"{k}={literal(v)}" for k, v in kwargs.items()]
    one_line = f"{func}({', '.join(parts)})"
    if len(one_line) <= width:
        return one_line
    body = "".join(f"    {p},\n" for p in parts)
    return f"{func}(\n{body})"


def assign(targets, expression: str) -> str:
    """``a, b = expression`` — `targets` a name or a sequence of names."""
    if isinstance(targets, str):
        return f"{targets} = {expression}"
    return f"{', '.join(targets)} = {expression}"


def script(lines: Iterable[str], app: str = "", what: str = "") -> str:
    """Join lines into a file's text, with a provenance header when `app` is given."""
    text = "\n".join(lines).rstrip() + "\n"
    if app:
        text = HEADER.format(app=app, what=what or "this file") + "\n" + text
    return text


def write_beside(path: str, text: str) -> str:
    """Write `text` as ``<path without extension>.py`` next to an export; returns the path written."""
    stem, _ = os.path.splitext(path)
    target = stem + ".py"
    with open(target, "w", encoding="utf-8") as f:
        f.write(text)
    return target


class CodePane:
    """A "Show code" block: a small toggle and, when open, the current script.

    A view calls :meth:`set` whenever its result changes; the text is also what
    the view's exports pass to :func:`write_beside`.
    """

    def __init__(self, label: str = "Show code", visible: bool = True):
        self.text = ""
        self.toggle = pn.widgets.Toggle(name=label, value=False, button_type="light", width=110,
                                        margin=(4, 0, 0, 0))
        self.copy_note = pn.pane.HTML(f'<span style="{MUTED_STYLE}">the calls behind this view — paste into a notebook</span>',
                                      margin=(10, 0, 0, 10), visible=False)
        self.code = pn.pane.Markdown("", sizing_mode="stretch_width", visible=False, margin=(0, 0, 0, 0))
        self.toggle.param.watch(self._on_toggle, "value")
        self.visible = visible

    def _on_toggle(self, event) -> None:
        self.code.visible = self.copy_note.visible = bool(event.new)

    def set(self, lines: Iterable[str] | str) -> None:
        """Replace the script with `lines` (a string, or lines to join)."""
        self.text = lines if isinstance(lines, str) else "\n".join(lines)
        self.code.object = f"```python\n{self.text.rstrip()}\n```"

    def panel(self) -> pn.Column:
        return pn.Column(pn.Row(self.toggle, self.copy_note), self.code, sizing_mode="stretch_width",
                         visible=self.visible)

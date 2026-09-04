"""
Forms generated from :class:`pmagpy.convert_registry.Field` descriptions.

A converter says what it needs as Fields; this module turns them into widgets
and reads the widgets back into the plain dict :func:`convert_registry.convert_files`
takes. Nothing about a particular converter lives here — a new format in the
registry gets its form for free.

The widget for each kind:

- ``text``: a text input; ``int``/``float`` with a default: numeric inputs;
  a ``float`` with no default (latitude to fill in later): a text input left blank.
- ``bool``: a checkbox.  ``choice``: a select showing the labels.
- ``codes``: a multi-choice; the value is the list of codes chosen.
- ``naming``: a select of the sample-naming conventions and, for the two that
  need a character count, a number beside it; the value is ``'1'``, ``'4-2'`` …
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import panel as pn

from pmagpy.convert_registry import Field, NAMING_CONVENTIONS

WIDGET_WIDTH = 300
Z_WIDTH = 100             # the character count beside a naming-convention select


class Form:
    """Widgets for a sequence of Fields, and their values as one dict.

    Args:
        fields: what to ask, in order.
        values: starting values by field name, over the fields' defaults —
            what the analyst typed last time, say.
        width: each widget's width; the form wraps them in rows.
    """

    def __init__(self, fields: Sequence[Field] = (), values: Dict[str, object] = None, width: int = WIDGET_WIDTH):
        self.width = width
        self.box = pn.FlexBox(sizing_mode="stretch_width", gap="4px 18px")
        self.widgets: Dict[str, pn.widgets.Widget] = {}
        self.extras: Dict[str, pn.widgets.Widget] = {}     # the Z count beside a naming select
        self.fields: List[Field] = []
        self.touched: set = set()                            # field names the analyst has set by hand
        self.set_fields(fields, values or {})

    def set_fields(self, fields: Sequence[Field], values: Dict[str, object] = None) -> None:
        """Rebuild the form for another set of fields, keeping values for names that carry over."""
        values = dict(values or {})
        for f in self.fields:                     # what the analyst set carries over; an untouched default does
            if f.name in self.touched:            # not, since the next format may default the other way
                values.setdefault(f.name, self.value_of(f.name))
        self.fields = list(fields)
        self.widgets, self.extras = {}, {}
        items = []
        for f in self.fields:
            start = values.get(f.name, f.default)
            w = self._widget(f, start)
            w.param.watch(lambda e, name=f.name: self.touched.add(name), "value")
            self.widgets[f.name] = w
            if f.kind == "naming":
                z = pn.widgets.IntInput(name="Z characters", value=_z_of(start), start=1, width=Z_WIDTH,
                                        visible=_needs_z(w.value), description="For conventions 4 and 7.")
                self.extras[f.name] = z
                w.param.watch(lambda e, z=z: setattr(z, "visible", _needs_z(e.new)), "value")
                items.append(pn.Row(w, z, width=self.width + 20, margin=0))     # one slot, like every other widget
            else:
                items.append(w)
        self.box.objects = items

    def _widget(self, f: Field, start) -> pn.widgets.Widget:
        kw = dict(name=f.label + (" *" if f.required else ""), width=self.width, description=f.help or None)
        if f.kind == "bool" and f.choices:        # both ways named: "Keep replicate…" / "Average replicate…"
            options = {label: value for value, label in f.choices}
            return pn.widgets.Select(options=options, value=bool(start), **kw)
        if f.kind == "bool":
            return pn.widgets.Checkbox(name=f.label, value=bool(start), width=self.width, margin=(20, 10, 5, 10))
        if f.kind == "choice":
            options = {label: value for value, label in f.choices}
            if f.default is None:                    # no default: the blank line comes first, so a required choice is a choice
                options = {"—": "", **options}
            value = start if start in options.values() else next(iter(options.values()), None)
            return pn.widgets.Select(options=options, value=value, **kw)
        if f.kind == "codes":
            options = {label: value for value, label in f.choices}
            chosen = list(start) if isinstance(start, (list, tuple)) else ([c for c in str(start).split(":") if c] if start else [])
            return pn.widgets.MultiChoice(options=options, value=chosen, placeholder="choose every protocol in the file", **kw)
        if f.kind == "naming":
            # the select shows the pattern; the full wording of every convention is the tooltip
            options = {f"{code} · {label.split(' — ')[0]}": code for code, label in NAMING_CONVENTIONS}
            legend = "\n".join(f"{code}: {label}" for code, label in NAMING_CONVENTIONS)
            code = str(start or "1").split("-")[0]
            return pn.widgets.Select(options=options, value=code if code in options.values() else "1",
                                     name=kw["name"], width=self.width - Z_WIDTH - 10,
                                     description=f"{f.help}\n{legend}" if f.help else legend)
        if f.kind == "int":
            return pn.widgets.IntInput(value=int(start) if start not in (None, "") else 0, **kw)
        if f.kind == "float" and start not in (None, ""):
            return pn.widgets.FloatInput(value=float(start), step=1, **kw)
        return pn.widgets.TextInput(value="" if start is None else str(start), placeholder="—" if f.kind == "float" else "", **kw)

    def value_of(self, name: str):
        w = self.widgets[name]
        f = next(f for f in self.fields if f.name == name)
        if f.kind == "naming":
            code = w.value
            return f"{code}-{self.extras[name].value}" if _needs_z(code) else code
        return w.value

    def values(self) -> Dict[str, object]:
        """Field name → value, ready for :func:`pmagpy.convert_registry.convert_files`."""
        return {name: self.value_of(name) for name in self.widgets}

    def missing(self) -> List[str]:
        """Labels of required fields left empty."""
        return [f.label for f in self.fields if f.required and self.value_of(f.name) in (None, "", [], ())]

    def panel(self) -> pn.FlexBox:
        return self.box


def _needs_z(code) -> bool:
    return str(code) in ("4", "7")


def _z_of(start) -> int:
    text = str(start or "")
    return int(text.split("-")[1]) if "-" in text and text.split("-")[1].isdigit() else 1

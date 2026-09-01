"""
The Home page: one directory as its subject, the workflow as a strip, the
applications as a list of doors.

Home reads everything it says from an :class:`~pmagpy_apps.inventory.Inventory`
and renders it as HTML on the shared shell. It has three faces, decided by what
the directory holds — a MagIC contribution, lab files not yet converted, or
nothing — and the same layout in all three. There is no form on it; the one
control is "Change directory…", which opens the dialog in :class:`OpenDirectory`.
"""
from __future__ import annotations

import html
import importlib.util
import os
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional
from urllib.parse import quote

import panel as pn
import param

from pmagpy_panel import datasets, runtime
from pmagpy_panel.theme import MUTED_STYLE
from . import APP
from .inventory import Inventory, take_inventory

FAIL_COLOR = "#c0392b"

# ----- which applications there are ------------------------------------------------


@dataclass(frozen=True)
class Application:
    """A door on the Analyze list.

    Attributes:
        name: as shown on the page.
        app_id: the served path (``/<app_id>``) and the package that serves it.
        kinds: the experiment kinds (inventory keys) it can work on; the door is
            shut, with the reason, when the directory has none of them.
        absent: what to say when the directory has none of those kinds.
    """
    name: str
    app_id: str
    kinds: tuple
    absent: str

    @property
    def built(self) -> bool:
        """The application's package can be imported: the door leads somewhere."""
        return importlib.util.find_spec(self.app_id) is not None


APPLICATIONS = (
    Application("Directions", "pmagpy_directions", ("demag",), "no demagnetization steps in this directory"),
    Application("Intensity", "pmagpy_intensity", ("pi",), "no paleointensity experiments in this directory"),
    Application("Rock magnetism", "pmagpy_rockmag", ("hys", "bcr", "irm", "arm", "chi_t", "ms_t", "low_t"),
                "no rock-magnetic measurements in this directory"),
    Application("FORC", "pmagpy_forc", ("forc",), "no FORC measurements in this directory"),
    Application("Anisotropy", "pmagpy_anisotropy", ("aniso",), "no anisotropy experiments in this directory"),
)


def app_link(app_id: str, directory: str) -> str:
    """The URL that opens an application on a directory, on the server this page came from."""
    return f"/{app_id}?dir={quote(directory)}"


def home_link(directory: str) -> str:
    return app_link(APP.app_id, directory)


# ----- the session -------------------------------------------------------------------


class HubSession(param.Parameterized):
    """The directory this session holds, and what is in it.

    ``landing`` is True while the page shows the directory it opened on by
    default — nothing asked for on the URL or in the environment. Home lists the
    recent directories only then; once the user has picked one, the page is
    about that directory.
    """
    directory = param.String(default="")
    status = param.String(default="")
    landing = param.Boolean(default=True)

    def __init__(self, directory: str, recent_file: str = "", landing: bool = True, **params):
        super().__init__(**params)
        self.recent_file = recent_file
        self.inventory: Inventory = Inventory(directory="")
        self.load(directory or os.getcwd(), remember=not landing)   # nothing asked for, no example found: start where the server runs
        self.landing = landing

    def load(self, directory: str, remember: bool = True) -> bool:
        """Take the directory's inventory and make it the session's. False when it is not a directory."""
        inv = take_inventory(directory)
        if not os.path.isdir(inv.directory):
            self.status = inv.error
            return False
        self.inventory = inv
        if remember and self.recent_file:
            datasets.remember_recent(self.recent_file, inv.directory)
        self.status = _status(inv)
        self.landing = False
        self.directory = inv.directory     # last: watchers rebuild the page from the new inventory
        return True

    def recent(self) -> List[str]:
        """Recently opened directories that still exist, most recent first."""
        if not self.recent_file:
            return []
        return [d for d in datasets.load_recent(self.recent_file) if os.path.isdir(d)]


def _status(inv: Inventory) -> str:
    if inv.is_magic:
        n = len([t for t in inv.tables if t != "contribution"])
        return f"{inv.name} loaded · {n} tables"
    if inv.is_empty:
        return f"{inv.name} · empty"
    return f"{inv.name} · no MagIC tables yet"


# ----- rendering -----------------------------------------------------------------------

CSS = """
:host { --accent:#1f4e9c; --ink:#2b2b2b; --muted:#6b7280; --line:#e3e6ea; --ok:#2e8b57; --warn:#d97706; --off:#9aa1ab; }
.home { font-size:15px; color:var(--ink) }
.section { font-weight:600; font-size:.78rem; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); margin:0 0 8px }
.home h1 { font-size:2rem; font-weight:600; margin:2px 0 4px; letter-spacing:-.01em }
.path { color:var(--muted); font-size:.85rem; font-family:ui-monospace,Menlo,monospace }
.ref { color:var(--muted); font-size:.9rem; margin-top:6px }
.ref a { color:var(--accent); text-decoration:none }
.kpi { display:flex; gap:22px; flex-wrap:wrap; font-size:.95rem; margin:16px 0 4px; font-variant-numeric:tabular-nums }
.kpi b { font-weight:600 }
.kpi .sep { color:#c9ced6 }
.kinds { display:flex; gap:8px; flex-wrap:wrap; margin:10px 0 0 }
.kind { border:1px solid var(--line); background:#fff; border-radius:999px; padding:3px 10px; font-size:.82rem }
.kind span { color:var(--muted) }
.empty { color:var(--muted); font-size:.95rem; margin:14px 0 0; max-width:62ch; line-height:1.5 }
.empty code { font-size:.9em }
.strip { display:grid; grid-template-columns:repeat(4,1fr); margin:28px 0 0; border:1px solid var(--line); border-radius:8px; background:#fff; overflow:hidden }
.stage { padding:14px 18px; border-right:1px solid var(--line); position:relative; min-height:74px }
.stage:last-child { border-right:0 }
.stage.next { background:#eef3fb }
.stage .name { font-weight:600; font-size:.95rem; display:flex; align-items:center; gap:8px }
.stage .state { font-size:.85rem; color:var(--muted); margin-top:4px; padding-right:8px }
.dot { width:9px; height:9px; border-radius:50%; display:inline-block; flex:none }
.dot.ok { background:var(--ok) } .dot.warn { background:var(--warn) } .dot.off { background:#d5d9df; border:1px solid #b9bfc7 }
.bars { display:flex; flex-direction:column; gap:8px }
.bar { background:#fff; border:1px solid var(--line); border-radius:8px; padding:12px 16px; display:flex; align-items:center; gap:16px;
       border-left:4px solid var(--accent); color:inherit; text-decoration:none }
.bar h3 { margin:0; font-size:1rem; font-weight:600; width:170px; flex:none }
.bar .fact { font-size:.9rem; color:var(--muted); flex:1 }
.bar .open { color:var(--accent); font-weight:600; font-size:.9rem; white-space:nowrap }
a.bar:hover { border-color:#b9c6dd; box-shadow:0 1px 4px rgba(31,78,156,.12) }
.bar.disabled { border-left-color:#d5d9df; background:#fbfbfc }
.bar.disabled h3 { color:#7b8390 }
.bar.disabled .open { color:var(--off); font-weight:500 }
.box { background:#fff; border:1px solid var(--line); border-radius:8px; padding:12px 16px; margin-bottom:18px }
.box table { border-collapse:collapse; width:100%; font-size:.88rem }
.box td { padding:3px 0; border-bottom:1px solid #f0f2f4 }
.box tr:last-child td { border-bottom:0 }
.box td.n { text-align:right; color:var(--muted); font-variant-numeric:tabular-nums; white-space:nowrap; padding-left:12px }
.box td.file { font-family:ui-monospace,Menlo,monospace; font-size:.82rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:220px }
.box .none { color:var(--muted); font-size:.88rem }
.recent { margin:0; padding:0 }
.recent li { list-style:none; padding:5px 0; font-size:.88rem; border-bottom:1px solid #f0f2f4 }
.recent li:last-child { border-bottom:0 }
.recent li a { color:var(--ink); text-decoration:none } .recent li a:hover { color:var(--accent) }
.recent li .p { color:var(--muted); font-size:.78rem; font-family:ui-monospace,Menlo,monospace; display:block;
                overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
"""


def fmt(n: int) -> str:
    return f"{n:,}"


def shorten_home(path: str) -> str:
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home) else path


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def heading_html(inv: Inventory) -> str:
    label = "MagIC directory" if inv.is_magic else "Directory"
    lines = [f'<div class="section">{label}</div>', f"<h1>{_esc(inv.name)}</h1>",
             f'<div class="path">{_esc(shorten_home(inv.directory))}</div>']
    c = inv.contribution
    if inv.is_magic and c:
        bits = []
        if c.get("id"):
            bits.append(f"MagIC contribution {_esc(c['id'])}")
        if c.get("reference"):
            ref = c["reference"]
            bits.append(f'<a href="https://doi.org/{_esc(ref)}" target="_blank">doi:{_esc(ref)}</a>'
                        if ref[:3] == "10." else _esc(ref))
        if c.get("contributor"):
            bits.append(_esc(c["contributor"]))
        if bits:
            lines.append(f'<div class="ref">{" · ".join(bits)}</div>')
    elif inv.is_empty:
        lines.append('<div class="ref">Empty</div>')
    elif not inv.is_magic:
        lines.append('<div class="ref">No MagIC tables yet</div>')
    return f'<div class="home">{"".join(lines)}</div>'


def facts_html(inv: Inventory) -> str:
    """The count line and the experiment chips, or the paragraph that says what to do instead."""
    if inv.is_magic:
        items = [f"<span><b>{fmt(inv.counts[k])}</b> {k if inv.counts[k] != 1 else k[:-1]}</span>"
                 for k in ("locations", "sites", "samples", "specimens", "measurements") if inv.counts.get(k)]
        kpi = '<div class="kpi">' + '<span class="sep">·</span>'.join(items) + "</div>"
        chips = "".join(
            f'<span class="kind">{_esc(k.label)} <span>{fmt(k.specimens)} specimen{"s" if k.specimens != 1 else ""}'
            f'{" · " + _esc(k.detail) if k.detail else ""}</span></span>' for k in inv.kinds)
        return f'<div class="home">{kpi}<div class="kinds">{chips}</div></div>'
    if inv.is_empty:
        text = ("Nothing here yet. Copy your measurement files into this directory and convert them, or download "
                "a published contribution from MagIC by its ID or DOI. Either way the MagIC tables land in this "
                "directory and this page fills in.")
    else:
        n = len(inv.files)
        what = {"CIT": f"look like CIT specimen files with a <code>.sam</code> index",
                "JR6": "look like JR6 files",
                "MagIC contribution file": "include a MagIC contribution file, which unpacks into the tables"}
        guess = f" They {what[inv.format_guess]}." if inv.format_guess in what else ""
        text = (f"{fmt(n)} file{'s' if n != 1 else ''}, none of them MagIC tables.{guess} Convert them on the "
                f"Import page, and this page fills in as the tables appear.")
    return f'<div class="home"><p class="empty">{text}</p></div>'


def stages(inv: Inventory) -> list:
    """(name, state class, one line, is-next) for Import → Metadata → Analyze → Upload."""
    if not inv.is_magic:
        if inv.is_empty:
            imp = ("warn", "convert files, or download from MagIC")
        else:
            n = len(inv.files)
            imp = ("warn", f"{fmt(n)} file{'s' if n != 1 else ''} to convert" + (f" · {inv.format_guess}?" if inv.format_guess else ""))
        return [("Import", *imp, True), ("Metadata", "off", "after import", False),
                ("Analyze", "off", "after import", False), ("Upload", "off", "after import", False)]
    others = [f for f in inv.files if f.role]
    imp = ("warn", f"{len(others)} file{'s' if len(others) != 1 else ''} not yet converted · {inv.format_guess}?") if others \
        else ("ok", "nothing waiting to convert")
    if inv.gaps:
        g = inv.gaps[0]
        more = len(inv.gaps) - 1
        meta = ("warn", f"{g.label} missing ({fmt(g.n)})" + (f" · {more} more gap{'s' if more != 1 else ''}" if more else ""))
    else:
        meta = ("ok", "no gaps found")
    a = inv.analysis
    parts = []
    if a.get("specimens_interpreted"):
        parts.append(f"{fmt(a['specimens_interpreted'])} specimens interpreted")
    if a.get("site_means"):
        parts.append(f"{fmt(a['site_means'])} site means")
    if a.get("site_intensities"):
        parts.append(f"{fmt(a['site_intensities'])} site intensities")
    ana = ("ok", " · ".join(parts)) if parts else ("warn", "nothing interpreted yet")
    return [("Import", *imp, False), ("Metadata", *meta, False), ("Analyze", *ana, not parts),
            ("Upload", "off", "not validated yet", False)]


def strip_html(inv: Inventory) -> str:
    cells = "".join(
        f'<div class="stage{" next" if nxt else ""}"><div class="name"><span class="dot {cls}"></span>{name}</div>'
        f'<div class="state">{_esc(line)}</div></div>' for name, cls, line, nxt in stages(inv))
    return f'<div class="home"><div class="strip">{cells}</div></div>'


def bars_html(inv: Inventory, applications=APPLICATIONS) -> str:
    bars = []
    for app in applications:
        present = [inv.kind(k) for k in app.kinds if inv.kind(k)]
        if not inv.is_magic:
            bars.append(_bar(app.name, "no measurements yet", None))
        elif not present:
            bars.append(_bar(app.name, app.absent, None))
        elif not app.built:
            bars.append(_bar(app.name, f"{_qualifier(present)} · not built yet", None, "Not yet"))
        else:
            bars.append(_bar(app.name, _qualifier(present), app_link(app.app_id, inv.directory)))
    return f'<div class="home"><div class="section">Analyze</div><div class="bars">{"".join(bars)}</div></div>'


def _qualifier(kinds) -> str:
    """What an application would open: 'AF and thermal demagnetization', 'Thellier experiments · IZZI, ZI'."""
    words = []
    for k in kinds:
        if k.key == "demag":
            words.append((" and ".join(k.details) + " demagnetization") if k.details else "demagnetization")
        elif k.key == "pi":
            words.append(f"{k.label} experiments" + (f" · {k.detail}" if k.detail else ""))
        else:
            label = k.label
            if label[1:] == label[1:].lower():        # a plain word reads on in the sentence; FORC, IRM, Ms–T keep their capitals
                label = label[:1].lower() + label[1:]
            words.append(label + (f" ({k.detail})" if k.detail else ""))
    return ", ".join(words)


def _bar(name: str, fact: str, href: Optional[str], shut: str = "—") -> str:
    if href:
        return (f'<a class="bar" href="{_esc(href)}"><h3>{_esc(name)}</h3><div class="fact">{_esc(fact)}</div>'
                f'<div class="open">Open →</div></a>')
    return (f'<div class="bar disabled"><h3>{_esc(name)}</h3><div class="fact">{_esc(fact)}</div>'
            f'<div class="open">{shut}</div></div>')


def aside_html(inv: Inventory, recent: List[str]) -> str:
    if inv.is_magic:
        rows = "".join(f'<tr><td class="file">{t}.txt</td><td class="n">{fmt(inv.tables[t].rows)}{" rows" if i == 0 else ""}</td></tr>'
                       for i, t in enumerate(n for n in ("measurements", "specimens", "samples", "sites", "locations",
                                                         "ages", "criteria", "images") if n in inv.tables))
        first = f'<div class="section">Tables</div><div class="box"><table>{rows}</table></div>'
    else:
        shown = inv.files[:6]
        rows = "".join(f'<tr><td class="file" title="{_esc(f.name)}">{_esc(f.name)}</td><td class="n">{_esc(f.role)}</td></tr>' for f in shown)
        if len(inv.files) > len(shown):
            rows += f'<tr><td class="file" style="color:var(--muted)">and {len(inv.files) - len(shown)} more</td><td class="n"></td></tr>'
        if inv.folders and not inv.files:
            rows = f'<tr><td class="none">{inv.folders} folder{"s" if inv.folders != 1 else ""}, no files</td></tr>'
        body = f"<table>{rows}</table>" if rows else '<div class="none">none</div>'
        first = f'<div class="section">Files</div><div class="box">{body}</div>'
    items = "".join(
        f'<li><a href="{_esc(home_link(d))}">{_esc(os.path.basename(d.rstrip(os.sep)) or d)}</a>'
        f'<span class="p" title="{_esc(d)}">{_esc(shorten_home(d))}</span></li>'
        for d in recent if d != inv.directory)
    second = (f'<div class="section">Recent</div><div class="box"><ul class="recent">{items}</ul></div>' if items else "")
    return f'<div class="home">{first}{second}</div>'


# ----- the view ------------------------------------------------------------------------


class HomeView:
    """Home as Panel objects, rebuilt whenever the session's directory changes."""

    def __init__(self, session: HubSession):
        self.s = session
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.facts = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.strip = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.bars = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.aside = pn.pane.HTML("", stylesheets=[CSS], width=340, sizing_mode="fixed")
        self.change_btn = pn.widgets.Button(name="Change directory…", button_type="primary", width=170,
                                            margin=(30, 0, 0, 0))
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    def refresh(self) -> None:
        inv = self.s.inventory
        self.heading.object = heading_html(inv)
        self.facts.object = facts_html(inv)
        self.strip.object = strip_html(inv)
        self.bars.object = bars_html(inv)
        self.aside.object = aside_html(inv, self.s.recent() if self.s.landing else [])
        self.change_btn.button_type = "primary" if inv.is_magic else "default"

    def panel(self) -> pn.Column:
        return pn.Column(
            pn.Row(self.heading, self.change_btn, sizing_mode="stretch_width"),
            self.facts, self.strip,
            pn.Row(self.bars, pn.Spacer(width=28, sizing_mode="fixed"), self.aside, sizing_mode="stretch_width",
                   margin=(28, 0, 0, 0)),
            sizing_mode="stretch_width", max_width=1100, margin=(18, 40, 40, 40),
        )


# ----- opening a different directory -----------------------------------------------------


class OpenDirectory:
    """The "Change directory…" dialog: the system folder dialog, the recent list, a path field.

    Any existing directory can be opened — Home is where a directory with nothing
    in it starts its life. The system dialog runs as a coroutine
    (:func:`pmagpy_panel.runtime.choose_directory`), so the server keeps serving
    while it is open.

    This is the hub's own until the shared ``DirectoryChooser`` lands on this
    branch; the widgets and their order are the same as the applications' so the
    swap is mechanical.
    """

    def __init__(self, session: HubSession, chooser_stub: str = ""):
        self.s = session
        self.stub = chooser_stub
        self.on_opened: Optional[Callable[[], None]] = None
        app = {"darwin": "Finder", "win32": "Explorer"}.get(sys.platform, "the system dialog")
        available = runtime.native_chooser_available(stub=chooser_stub)
        self.native_btn = pn.widgets.Button(name=f"Browse with {app}…", button_type="primary", width=220,
                                            disabled=not available)
        self.recent = pn.widgets.Select(name="Recent directories", options=[], size=6, sizing_mode="stretch_width",
                                        stylesheets=["select { max-width: 100%; }"])
        self.path = pn.widgets.TextInput(name="Directory", value=session.directory, sizing_mode="stretch_width")
        self.open_btn = pn.widgets.Button(name="Open", button_type="success", width=120)
        self.message = pn.pane.HTML("", sizing_mode="stretch_width")
        self.native_btn.on_click(self._browse)
        self.recent.param.watch(lambda e: setattr(self.path, "value", e.new) if e.new else None, "value")
        self.open_btn.on_click(self.open)
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    def refresh(self) -> None:
        self.recent.options = {shorten_home(d): d for d in self.s.recent()}
        self.path.value = self.s.directory

    async def _browse(self, event=None) -> None:
        self.native_btn.disabled = True
        self.message.object = f'<div style="{MUTED_STYLE}">Choose a folder in the dialog that just opened …</div>'
        start = os.path.expanduser(self.path.value.strip()) or self.s.directory
        try:
            chosen = await runtime.choose_directory(start, prompt="Choose a directory", stub=self.stub)
        finally:
            self.native_btn.disabled = False
        if chosen:
            self.path.value = chosen
            self.open()
        else:
            self.message.object = f'<div style="{MUTED_STYLE}">No folder chosen.</div>'

    def open(self, event=None) -> bool:
        target = os.path.abspath(os.path.expanduser(self.path.value.strip()))
        if not self.path.value.strip():
            return False
        if not os.path.isdir(target):
            self.message.object = f'<div style="color:{FAIL_COLOR}"><code>{_esc(target)}</code> is not a directory</div>'
            return False
        if not self.s.load(target):
            self.message.object = f'<div style="color:{FAIL_COLOR}">{_esc(self.s.status)}</div>'
            return False
        self.message.object = ""
        location = runtime.location()
        if location is not None:
            location.search = f"?dir={quote(target)}"     # so a reload, or a bookmark, comes back here
        if self.on_opened:
            self.on_opened()
        return True

    def modal(self) -> pn.Column:
        return pn.Column(
            pn.pane.HTML('<h3 style="margin:0 0 6px 0">Open a directory</h3>'
                         f'<div style="{MUTED_STYLE}">A MagIC directory, a folder of files to convert, or an empty one to start in.</div>'),
            pn.Row(self.native_btn, self.message),
            self.recent, pn.Row(self.path, self.open_btn),
            width=720, sizing_mode="fixed")

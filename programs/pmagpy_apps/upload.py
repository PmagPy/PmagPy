"""
The Upload page: check the tables, build the one file MagIC takes, ask MagIC to validate it.

What Pmag GUI's box 3 and Export menu did. Every step is a call into
:mod:`pmagpy.magic_upload`; the page's job is to run the slow ones (the
offline check of a large measurements table, MagIC's validator over the
network) off the event loop and say what came back — findings by table for
the offline check, MagIC's own messages with row numbers for the online one.
The upload file lands in the study directory, where Home's inventory finds it
and the Upload stage reports it; the file itself goes to MagIC by hand, at
MagIC's upload page, since uploading into a private workspace needs a login
PmagPy does not hold.
"""
from __future__ import annotations

import asyncio
import html
import os
from datetime import datetime
from typing import Dict, List

import panel as pn

from pmagpy import magic_metadata as mm
from pmagpy import magic_upload as mu
from pmagpy_panel.theme import MUTED_STYLE
from .home import CSS, fmt, shorten_home
from .metadata import FAIL_COLOR, OK_COLOR, WARN_COLOR

MAGIC_UPLOAD_URL = "https://www2.earthref.org/MagIC/upload"
MAX_ITEMS = 40          # findings listed per table before "… and n more"

REPORT_CSS = """
.report { font-size:.88rem; color:#2b2b2b; line-height:1.45; max-height:340px; overflow:auto;
          border:1px solid #e3e6ea; border-radius:6px; padding:10px 14px; background:#fafbfc }
.report h4 { margin:10px 0 2px; font-size:.95rem; font-weight:650 }
.report h4:first-child { margin-top:0 }
.report h4 span { color:#6b7280; font-weight:400; font-size:.85rem }
.report ul { margin:2px 0 0; padding-left:18px }
.report li { padding:1px 0; word-break:break-word }
.report b { font-family:ui-monospace,Menlo,monospace; font-weight:600 }
.report .rows { color:#6b7280 }
.report .ok { color:#1a7f5a }
.report .warn { color:#b45309 }
.step { font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:#6b7280; margin:26px 0 0 }
.step-note { font-size:.88rem; color:#4b5563; margin:2px 0 8px }
.files { font-size:.88rem; color:#2b2b2b }
.files li { padding:1px 0 }
.files b { font-family:ui-monospace,Menlo,monospace; font-weight:600 }
.link a { color:#1f4e9c; font-weight:600; text-decoration:none }
.link a:hover { text-decoration:underline }
"""


# ----- rendering ------------------------------------------------------------------------------
def size_text(nbytes: int) -> str:
    return f"{nbytes / 1e6:.1f} MB" if nbytes >= 1e6 else f"{nbytes / 1e3:.0f} kB"


def _rows(rows: List[int]) -> str:
    if not rows:
        return ""
    shown = ", ".join(str(r) for r in rows[:12]) + (f" … {len(rows) - 12} more" if len(rows) > 12 else "")
    return f' <span class="rows">row{"s" if len(rows) != 1 else ""} {html.escape(shown)}</span>'


def findings_html(findings: Dict[str, List[mm.Finding]]) -> str:
    """PmagPy's offline check, one heading per table; a table with nothing to say gets one green line."""
    if not findings:
        return ""
    parts = []
    for table, items in findings.items():
        n = len(items)
        if not items:
            parts.append(f'<h4>{html.escape(table)} <span class="ok">passes</span></h4>')
            continue
        parts.append(f'<h4>{html.escape(table)} <span>{fmt(n)} finding{"s" if n != 1 else ""}</span></h4><ul>')
        for f in items[:MAX_ITEMS]:
            where = f"<b>{html.escape(f.row)}</b> · " if f.row else ""
            parts.append(f"<li>{where}<b>{html.escape(f.column)}</b>: {html.escape(f.problem)}</li>")
        if n > MAX_ITEMS:
            parts.append(f'<li class="rows">… and {fmt(n - MAX_ITEMS)} more</li>')
        parts.append("</ul>")
    return f'<div class="report">{"".join(parts)}</div>'


def report_html(report: mu.OnlineReport) -> str:
    """What MagIC's validator said, errors by table then warnings."""
    if not report.reached:
        return f'<div class="report"><span class="warn">{html.escape(report.trouble)}</span></div>'
    parts = []
    if not report.errors:
        parts.append('<h4><span class="ok">MagIC finds no errors</span></h4>')
    for table, issues in report.by_table().items():
        n = len(issues)
        parts.append(f'<h4>{html.escape(table or "file")} <span>{fmt(n)} error{"s" if n != 1 else ""}</span></h4><ul>')
        for issue in issues[:MAX_ITEMS]:
            col = f"<b>{html.escape(issue.column)}</b>: " if issue.column else ""
            parts.append(f"<li>{col}{html.escape(issue.message)}{_rows(issue.rows)}</li>")
        if n > MAX_ITEMS:
            parts.append(f'<li class="rows">… and {fmt(n - MAX_ITEMS)} more</li>')
        parts.append("</ul>")
    if report.warnings:
        n = len(report.warnings)
        parts.append(f'<h4>warnings <span>{fmt(n)}</span></h4><ul>')
        for issue in report.warnings[:MAX_ITEMS]:
            where = " · ".join(html.escape(x) for x in (issue.table, issue.column) if x)
            parts.append(f"<li>{'<b>' + where + '</b>: ' if where else ''}{html.escape(issue.message)}{_rows(issue.rows)}</li>")
        parts.append("</ul>")
    return f'<div class="report">{"".join(parts)}</div>'


def upload_files_html(directory: str, names: List[str]) -> str:
    """The upload files already in the directory, newest first, with size and date."""
    if not names:
        return ""
    items = []
    for n in names:
        path = os.path.join(directory, n)
        try:
            size = size_text(os.path.getsize(path))
            when = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%-d %b %Y %H:%M")
        except OSError:
            continue
        items.append(f"<li><b>{html.escape(n)}</b> · {size} · {when}</li>")
    return f'<ul class="files">{"".join(items)}</ul>'


def export_html(result: mu.ExportResult, directory: str) -> str:
    parts = []
    if result.files:
        parts.append("<ul>" + "".join(f"<li><b>{html.escape(os.path.relpath(f, directory))}</b></li>" for f in result.files) + "</ul>")
    if result.skipped:
        parts.append(f'<div class="rows">nothing to export from {", ".join(html.escape(t) for t in result.skipped)}</div>')
    warns = [ln[4:].replace(directory + os.sep, "") for ln in result.log.splitlines() if ln.startswith("-W- ")]
    if warns:
        parts.append('<div class="warn">' + "<br>".join(html.escape(w) for w in warns) + "</div>")
    return f'<div class="report">{"".join(parts)}</div>' if parts else ""


# ----- the page -------------------------------------------------------------------------------
class UploadView:
    """Check → build → validate → export, each a button with its report beneath."""

    def __init__(self, session):
        self.s = session
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.home_btn = pn.widgets.Button(name="← Home", button_type="default", width=110, margin=(30, 0, 0, 0))
        self.note = pn.pane.HTML("", sizing_mode="stretch_width", min_height=22)

        self.check_btn = pn.widgets.Button(name="Check tables", button_type="default", width=130)
        self.check_msg = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24, margin=(5, 10))
        self.check_pane = pn.pane.HTML("", stylesheets=[REPORT_CSS], sizing_mode="stretch_width")

        self.build_btn = pn.widgets.Button(name="Build upload file", button_type="success", width=160)
        self.build_msg = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24, margin=(5, 10))
        self.files_pane = pn.pane.HTML("", stylesheets=[REPORT_CSS], sizing_mode="stretch_width")

        self.file = pn.widgets.Select(name="Upload file", options=[], width=380)
        self.validate_btn = pn.widgets.Button(name="Validate with MagIC", button_type="default", width=170,
                                              margin=(23, 5, 5, 5))
        self.validate_msg = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24, margin=(23, 10, 5, 10))
        self.validate_pane = pn.pane.HTML("", stylesheets=[REPORT_CSS], sizing_mode="stretch_width")
        self.link = pn.pane.HTML(
            f'<div class="link">Then upload it to a private workspace at '
            f'<a href="{MAGIC_UPLOAD_URL}" target="_blank" rel="noopener">MagIC</a> ↗</div>',
            stylesheets=[REPORT_CSS], sizing_mode="stretch_width", margin=(8, 10, 0, 10))

        self.export_kind = pn.widgets.RadioButtonGroup(options={"Excel": False, "LaTeX": True}, value=False,
                                                       button_type="default", button_style="outline")
        self.export_btn = pn.widgets.Button(name="Export publication tables", button_type="default", width=200)
        self.export_msg = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24, margin=(5, 10))
        self.export_pane = pn.pane.HTML("", stylesheets=[REPORT_CSS], sizing_mode="stretch_width")

        self.check_btn.on_click(self.check)
        self.build_btn.on_click(self.build)
        self.validate_btn.on_click(self.validate)
        self.export_btn.on_click(self.export)
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    # ----- following the directory --------------------------------------------------------------
    def refresh(self) -> None:
        inv = self.s.inventory
        self.heading.object = (f'<div class="home"><div class="section">Upload</div><h1>{html.escape(inv.name)}</h1>'
                               f'<div class="path">{html.escape(shorten_home(inv.directory))}</div></div>')
        present = mu.present_tables(inv.directory) if inv.is_magic else []
        bits = [f"{t} ({fmt(inv.tables[t].rows)})" if t in inv.tables else t for t in present]
        text = "tables to upload: " + ", ".join(bits) if bits else "no MagIC tables here"
        self.note.object = f'<div style="{MUTED_STYLE}">{html.escape(text)}</div>'
        self.check_btn.disabled = self.build_btn.disabled = self.export_btn.disabled = not present
        self._list_files()

    def _list_files(self) -> None:
        names = self.s.inventory.uploads
        self.files_pane.object = upload_files_html(self.s.directory, names)
        self.file.options = names
        self.file.value = names[0] if names else None
        self.file.visible = self.validate_btn.visible = self.link.visible = bool(names)

    def reset(self) -> None:
        """A fresh page: the directory as it is now, last time's reports cleared."""
        self.refresh()
        for pane in (self.check_msg, self.check_pane, self.build_msg, self.validate_msg, self.validate_pane,
                     self.export_msg, self.export_pane):
            pane.object = ""
        self.home_btn.button_type = "default"

    # ----- the steps -----------------------------------------------------------------------------
    async def check(self, event=None) -> Dict[str, List[mm.Finding]]:
        """PmagPy's validator over every table (a big measurements table takes seconds)."""
        directory = self.s.directory
        self.check_btn.disabled = True
        _say(self.check_msg, "Checking …")
        try:
            findings = await asyncio.get_running_loop().run_in_executor(None, lambda: mu.check_offline(directory))
        except Exception as ex:                                   # the validator is deep; the page reports rather than dies
            _say(self.check_msg, html.escape(f"check failed: {ex}"), FAIL_COLOR)
            return {}
        finally:
            self.check_btn.disabled = False
        n = sum(len(v) for v in findings.values())
        bad = [t for t, v in findings.items() if v]
        if n:
            _say(self.check_msg, f"{fmt(n)} finding{'s' if n != 1 else ''} in {', '.join(bad)} · fix them on the Metadata page",
                 WARN_COLOR)
        else:
            _say(self.check_msg, f"all {len(findings)} tables pass PmagPy's check", OK_COLOR)
        self.check_pane.object = findings_html(findings)
        return findings

    async def build(self, event=None) -> bool:
        """Write the upload file into the directory and reload it so Home sees the file."""
        directory = self.s.directory
        self.build_btn.disabled = True
        _say(self.build_msg, "Building …")
        try:
            up = await asyncio.get_running_loop().run_in_executor(None, lambda: mu.build_upload_file(directory))
        except Exception as ex:
            _say(self.build_msg, html.escape(f"could not build the upload file: {ex}"), FAIL_COLOR)
            return False
        finally:
            self.build_btn.disabled = False
        if not self.s.load(directory):
            _say(self.build_msg, html.escape(self.s.status), FAIL_COLOR)
            return False
        _say(self.build_msg, f"<b>{html.escape(up.name)}</b> · {size_text(up.size)} · {len(up.tables)} tables", OK_COLOR)
        self.validate_pane.object = self.validate_msg.object = ""
        self.home_btn.button_type = "primary"
        return True

    async def validate(self, event=None) -> mu.OnlineReport:
        """Send the chosen upload file to MagIC's public validator (about a minute for a large study)."""
        name = self.file.value
        if not name:
            return mu.OnlineReport(reached=False, trouble="no upload file")
        path = os.path.join(self.s.directory, name)
        self.validate_btn.disabled = True
        _say(self.validate_msg, "MagIC is validating the file — around a minute for a large study …")
        try:
            report = await asyncio.get_running_loop().run_in_executor(None, lambda: mu.validate_online(path))
        finally:
            self.validate_btn.disabled = False
        if not report.reached:
            _say(self.validate_msg, html.escape(report.trouble), FAIL_COLOR)
        elif report.errors:
            n = len(report.errors)
            _say(self.validate_msg, f"MagIC reports {fmt(n)} error{'s' if n != 1 else ''} in {html.escape(name)}", FAIL_COLOR)
        else:
            _say(self.validate_msg, f"{html.escape(name)} passes MagIC's validation", OK_COLOR)
        self.validate_pane.object = report_html(report)
        return report

    async def export(self, event=None) -> mu.ExportResult:
        """Write the site, specimen and criteria publication tables beside the MagIC tables."""
        directory = self.s.directory
        latex = bool(self.export_kind.value)
        self.export_btn.disabled = True
        _say(self.export_msg, "Exporting …")
        try:
            result = await asyncio.get_running_loop().run_in_executor(
                None, lambda: mu.export_tables(directory, latex=latex))
        except Exception as ex:
            _say(self.export_msg, html.escape(f"export failed: {ex}"), FAIL_COLOR)
            return mu.ExportResult(log=str(ex))
        finally:
            self.export_btn.disabled = False
        n = len(result.files)
        _say(self.export_msg, f"{n} file{'s' if n != 1 else ''} written", OK_COLOR if n else WARN_COLOR)
        self.export_pane.object = export_html(result, directory)
        return result

    # ----- layout ------------------------------------------------------------------------------------
    def panel(self) -> pn.Column:
        def step(title, note):
            return pn.pane.HTML(f'<div class="step">{title}</div><div class="step-note">{note}</div>',
                                stylesheets=[REPORT_CSS], sizing_mode="stretch_width")
        return pn.Column(
            pn.Row(self.heading, self.home_btn, sizing_mode="stretch_width"),
            self.note,
            step("1 · Check", "PmagPy's offline check of every table against the MagIC data model."),
            pn.Row(self.check_btn, self.check_msg, sizing_mode="stretch_width"),
            self.check_pane,
            step("2 · Build", "One file with every table, written into this directory as "
                              "<i>&lt;location&gt;_&lt;date&gt;.txt</i>; columns MagIC does not take are dropped."),
            pn.Row(self.build_btn, self.build_msg, sizing_mode="stretch_width"),
            self.files_pane,
            step("3 · Validate", "MagIC's own validator, with the current data model, over the built file."),
            pn.Row(self.file, self.validate_btn, self.validate_msg, sizing_mode="stretch_width"),
            self.validate_pane,
            self.link,
            step("4 · Publication tables", f"Site, specimen and criteria tables for a manuscript, written into "
                                           f"<i>{mu.EXPORT_DIR}/</i> here."),
            pn.Row(self.export_kind, self.export_btn, self.export_msg, sizing_mode="stretch_width"),
            self.export_pane,
            sizing_mode="stretch_width", max_width=1100, margin=(18, 40, 40, 40),
        )


def _say(pane: pn.pane.HTML, text: str, color: str = "") -> None:
    style = f"color:{color}" if color else MUTED_STYLE
    pane.object = f'<div style="{style}">{text}</div>'

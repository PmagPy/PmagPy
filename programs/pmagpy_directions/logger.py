"""
The step logger: every measurement step of the current specimen, in
measurement order, as a compact table that stays visible next to the plots.

Interaction (mirrors the legacy Demag GUI):
* left click on a row  -> select the step: it is ringed on every plot, ↑ ↓ move it
* right click on a row -> toggle the measurement good/bad
* drag a header's right edge -> resize that column; double click -> the default widths

Implemented as a small custom component so that a right click is a real
event (Tabulator only exposes left clicks) and so that the rows can never be
re-sorted away from measurement order.
"""
from __future__ import annotations

import param
from panel.custom import JSComponent

#: the columns, in order (the keys of ``StepLogger.widths``)
COLUMNS = ("i", "step", "dec", "inc", "M", "csd")
MIN_WIDTH = 14         # a column dragged this narrow is out of the way
MAX_WIDTH = 600


def valid_widths(widths) -> dict:
    """``widths`` as ``StepLogger.widths`` takes them: a width in px for every column, or {} (the default)."""
    if not isinstance(widths, dict) or set(widths) != set(COLUMNS):
        return {}
    if not all(isinstance(w, (int, float)) and not isinstance(w, bool) for w in widths.values()):
        return {}
    return {c: int(max(MIN_WIDTH, min(MAX_WIDTH, widths[c]))) for c in COLUMNS}


class StepLogger(JSComponent):
    """Table of demagnetization steps with click / right-click events."""

    rows = param.List(default=[], doc="list of dicts: i, step, dec, inc, M, csd, q")
    highlight = param.Dict(default={}, doc="{'imin', 'imax', 'color'} of the current fit")
    marks = param.Dict(default={}, doc="{'imin', 'imax'} pending bound selection")
    selected = param.Integer(default=-1, doc="row (step index) selected, -1 for none; drawn and scrolled into view")
    clicked = param.Dict(default={}, doc="{'row', 'button', 'n'} last click (n increments)")
    widths = param.Dict(default={}, doc="{column: px} as the analyst dragged the columns; {} for the default, "
                                        "which fills the width with i and step fitted to their content")
    coord_label = param.String(default="")

    _esm = """
    const COLUMNS = [['i', 'i'], ['step', 'step'], ['dec', 'dec'], ['inc', 'inc'], ['M', 'M (Am²)'], ['csd', 'csd']];
    const MIN_WIDTH = %d, MAX_WIDTH = %d;

    export function render({ model }) {
      const root = document.createElement('div');
      root.className = 'step-logger';
      let counter = 0;
      let dragging = null;          // the widths while a column's edge is dragged

      // fixed widths: every column as wide as set, the table as wide as they add up to
      // (narrower: blank at the right; wider: the logger scrolls sideways)
      function applyWidths(table, w) {
        table.classList.add('fixed');
        table.style.width = COLUMNS.reduce((sum, [c]) => sum + w[c], 0) + 'px';
        table.querySelectorAll('col').forEach((col, k) => { col.style.width = w[COLUMNS[k][0]] + 'px'; });
      }

      function draw() {
        const h = model.highlight || {};
        const m = model.marks || {};
        let html = '<table><colgroup>' + COLUMNS.map(([c]) => `<col data-c="${c}">`).join('') +
                   '</colgroup><thead><tr>' +
                   COLUMNS.map(([c, label]) => `<th data-c="${c}">${label}<span class="grip" ` +
                               'title="drag to resize the column · double click: the default widths"></span></th>').join('') +
                   '</tr></thead><tbody>';
        for (const r of model.rows) {
          const cls = [];
          if (r.q === 'b') cls.push('bad');
          const inFit = h.imin !== undefined && r.i >= h.imin && r.i <= h.imax;
          if (inFit) cls.push('infit');
          if (m.imin === r.i) cls.push('bmin');
          if (m.imax === r.i) cls.push('bmax');
          if (model.selected === r.i) cls.push('sel');
          const style = inFit ? ` style="background:${h.color}26"` : '';
          const flag = r.q === 'b' ? '<span class="flag">bad</span>' : '';
          html += `<tr data-i="${r.i}" class="${cls.join(' ')}"${style}>` +
                  `<td class="num">${r.i}</td><td class="step">${r.step}${flag}</td>` +
                  `<td class="num">${r.dec}</td><td class="num">${r.inc}</td>` +
                  `<td class="num">${r.M}</td><td class="num">${r.csd}</td></tr>`;
        }
        root.innerHTML = html + '</tbody></table>';
        const w = dragging || model.widths || {};
        if (COLUMNS.every(([c]) => w[c] > 0)) applyWidths(root.querySelector('table'), w);
        const sel = root.querySelector('tr.sel');
        if (sel) sel.scrollIntoView({ block: 'nearest' });
      }

      root.addEventListener('click', (e) => {
        const tr = e.target.closest('tr[data-i]');
        if (!tr) return;
        model.clicked = { row: Number(tr.dataset.i), button: 'left', n: ++counter };
      });
      root.addEventListener('contextmenu', (e) => {
        const tr = e.target.closest('tr[data-i]');
        if (!tr) return;
        e.preventDefault();
        model.clicked = { row: Number(tr.dataset.i), button: 'right', n: ++counter };
      });
      // a drag starts from the widths on show (the default's, measured, the first time), so
      // nothing moves until the pointer does; the server hears of it once, on release
      root.addEventListener('mousedown', (e) => {
        const grip = e.target.closest('.grip');
        if (!grip || e.button !== 0) return;
        e.preventDefault();
        const table = root.querySelector('table');
        const key = grip.parentElement.dataset.c;
        dragging = {};
        table.querySelectorAll('thead th').forEach((th) => {
          dragging[th.dataset.c] = Math.round(th.getBoundingClientRect().width);
        });
        const startX = e.clientX, startW = dragging[key];
        let moved = false;
        grip.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        const onMove = (ev) => {
          moved = true;
          dragging[key] = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, Math.round(startW + ev.clientX - startX)));
          applyWidths(root.querySelector('table'), dragging);
        };
        // a click that did not move keeps the widths as they were (the default stays the default)
        const onUp = () => {
          document.removeEventListener('mousemove', onMove);
          document.removeEventListener('mouseup', onUp);
          document.body.style.cursor = '';
          const done = dragging;
          dragging = null;
          root.querySelectorAll('.grip.dragging').forEach((g) => g.classList.remove('dragging'));
          if (moved) model.widths = done;
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
      });
      root.addEventListener('dblclick', (e) => {
        if (e.target.closest('.grip')) model.widths = {};
      });
      model.on('rows', draw);
      model.on('highlight', draw);
      model.on('marks', draw);
      model.on('selected', draw);
      model.on('widths', draw);
      draw();
      return root;
    }
    """ % (MIN_WIDTH, MAX_WIDTH)

    _stylesheets = ["""
    .step-logger { font-family: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 12.5px;
                   overflow-y: auto; height: 100%; border: 1px solid #d0d4da; border-radius: 6px;
                   background: #fff; user-select: none; }
    .step-logger table { border-collapse: collapse; width: 100%; }
    .step-logger table.fixed { table-layout: fixed; }
    .step-logger thead th { position: sticky; top: 0; background: #f3f4f6; color: #374151; font-weight: 600;
                            text-align: right; padding: 5px 8px; border-bottom: 1px solid #d0d4da;
                            border-right: 1px solid #e3e6ea; white-space: nowrap; }
    .step-logger thead th:nth-child(2) { text-align: left; }
    /* by default i and step take what their content needs, the numbers share the rest */
    .step-logger table:not(.fixed) th:nth-child(-n+2) { width: 1%; }
    .step-logger .grip { position: absolute; top: 0; right: -3px; width: 7px; height: 100%; cursor: col-resize;
                         z-index: 1; }
    .step-logger .grip:hover, .step-logger .grip.dragging { background: #9aa1ab66; }
    .step-logger td { padding: 3px 8px; border-bottom: 1px solid #f0f1f3; white-space: nowrap; cursor: pointer; }
    .step-logger table.fixed th, .step-logger table.fixed td { overflow: hidden; text-overflow: ellipsis; }
    .step-logger td.num { text-align: right; font-variant-numeric: tabular-nums; }
    .step-logger td.step { text-align: left; font-weight: 500; }
    .step-logger tr:hover td { background: #eef3fb; }
    .step-logger tr.bad td { color: #9aa1ab; text-decoration: line-through; }
    .step-logger tr.bad .flag { text-decoration: none; margin-left: 6px; font-size: 10px; color: #c0392b;
                                border: 1px solid #c0392b; border-radius: 3px; padding: 0 3px; }
    .step-logger tr.sel td { font-weight: 700; background: #dbe4f3 !important; }
    .step-logger tr.sel td:first-child { box-shadow: inset 4px 0 0 #1f2937; }
    .step-logger tr.bmin td:first-child, .step-logger tr.bmax td:first-child { font-weight: 700; color: #1f4e9c; }
    .step-logger tr.bmin td:first-child::before { content: '⌈'; margin-right: 2px; }
    .step-logger tr.bmax td:first-child::before { content: '⌊'; margin-right: 2px; }
    """]

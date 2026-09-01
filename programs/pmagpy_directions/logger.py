"""
The step logger: every measurement step of the current specimen, in
measurement order, as a compact table that stays visible next to the plots.

Interaction (mirrors the legacy Demag GUI):
* left click on a row  -> first click sets the lower bound, second the upper
* right click on a row -> toggle the measurement good/bad

Implemented as a small custom component so that a right click is a real
event (Tabulator only exposes left clicks) and so that the rows can never be
re-sorted away from measurement order.
"""
from __future__ import annotations

import param
from panel.custom import JSComponent


class StepLogger(JSComponent):
    """Table of demagnetization steps with click / right-click events."""

    rows = param.List(default=[], doc="list of dicts: i, step, dec, inc, M, csd, q")
    highlight = param.Dict(default={}, doc="{'imin', 'imax', 'color'} of the current fit")
    marks = param.Dict(default={}, doc="{'imin', 'imax'} pending bound selection")
    clicked = param.Dict(default={}, doc="{'row', 'button', 'n'} last click (n increments)")
    coord_label = param.String(default="")

    _esm = """
    export function render({ model }) {
      const root = document.createElement('div');
      root.className = 'step-logger';
      let counter = 0;

      function draw() {
        const h = model.highlight || {};
        const m = model.marks || {};
        let html = '<table><thead><tr><th>i</th><th>step</th><th>dec</th><th>inc</th>' +
                   '<th>M (Am²)</th><th>csd</th></tr></thead><tbody>';
        for (const r of model.rows) {
          const cls = [];
          if (r.q === 'b') cls.push('bad');
          const inFit = h.imin !== undefined && r.i >= h.imin && r.i <= h.imax;
          if (inFit) cls.push('infit');
          if (m.imin === r.i) cls.push('bmin');
          if (m.imax === r.i) cls.push('bmax');
          const style = inFit ? ` style="background:${h.color}26"` : '';
          const flag = r.q === 'b' ? '<span class="flag">bad</span>' : '';
          html += `<tr data-i="${r.i}" class="${cls.join(' ')}"${style}>` +
                  `<td class="num">${r.i}</td><td class="step">${r.step}${flag}</td>` +
                  `<td class="num">${r.dec}</td><td class="num">${r.inc}</td>` +
                  `<td class="num">${r.M}</td><td class="num">${r.csd}</td></tr>`;
        }
        root.innerHTML = html + '</tbody></table>';
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
      model.on('rows', draw);
      model.on('highlight', draw);
      model.on('marks', draw);
      draw();
      return root;
    }
    """

    _stylesheets = ["""
    .step-logger { font-family: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 12.5px;
                   overflow-y: auto; height: 100%; border: 1px solid #d0d4da; border-radius: 6px;
                   background: #fff; user-select: none; }
    .step-logger table { border-collapse: collapse; width: 100%; }
    .step-logger thead th { position: sticky; top: 0; background: #f3f4f6; color: #374151; font-weight: 600;
                            text-align: right; padding: 5px 8px; border-bottom: 1px solid #d0d4da; }
    .step-logger thead th:nth-child(2) { text-align: left; }
    .step-logger td { padding: 3px 8px; border-bottom: 1px solid #f0f1f3; white-space: nowrap; cursor: pointer; }
    .step-logger td.num { text-align: right; font-variant-numeric: tabular-nums; }
    .step-logger td.step { text-align: left; font-weight: 500; }
    .step-logger tr:hover td { background: #eef3fb; }
    .step-logger tr.bad td { color: #9aa1ab; text-decoration: line-through; }
    .step-logger tr.bad .flag { text-decoration: none; margin-left: 6px; font-size: 10px; color: #c0392b;
                                border: 1px solid #c0392b; border-radius: 3px; padding: 0 3px; }
    .step-logger tr.bmin td:first-child, .step-logger tr.bmax td:first-child { font-weight: 700; color: #1f4e9c; }
    .step-logger tr.bmin td:first-child::before { content: '⌈'; margin-right: 2px; }
    .step-logger tr.bmax td:first-child::before { content: '⌊'; margin-right: 2px; }
    """]



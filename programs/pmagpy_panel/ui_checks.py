"""
Browser-level checks shared by the applications' Playwright suites (``ui_test.py``).

Nothing here imports Playwright: each function takes the suite's ``page``.
"""
from __future__ import annotations

import time

# Every animation frame, after it has been drawn, record where the plot handle
# is and how tall the figures above it are on screen. (A message posted from
# requestAnimationFrame is handled after that frame's layout, resize-observer
# callbacks and paint, so the log holds what was actually shown.)
_WATCH_PLOT_HANDLE = r"""() => {
  const deep = (root, pred, out = []) => {
    for (const e of root.querySelectorAll('*')) {
      if (pred(e)) out.push(e);
      if (e.shadowRoot) deep(e.shadowRoot, pred, out);
    }
    return out;
  };
  const bar = deep(document, e => e.classList && e.classList.contains('hsplitter'))
    .find(e => e.getBoundingClientRect().height > 0);
  if (!bar) return null;
  const block = bar.getRootNode().host.previousElementSibling;
  const figures = () => deep(block.shadowRoot, e => e.classList && e.classList.contains('bk-Figure'));
  const sample = () => {
    const top = block.getBoundingClientRect().top;
    const bottom = Math.max(...figures().map(f => f.getBoundingClientRect().bottom));
    window.__plotHandleLog.push({bar: bar.getBoundingClientRect().top, height: bottom - top});
  };
  window.__plotHandleLog = [];
  const channel = new MessageChannel();
  channel.port1.onmessage = sample;
  const tick = () => { channel.port2.postMessage(0); if (window.__plotHandleLog) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  const r = bar.getBoundingClientRect();
  return {x: r.left + r.width / 2, y: r.top + r.height / 2};
}"""


# Each figure's canvas against the figure's own box: the largest departure of the
# ratio of their widths from 1. Bokeh sizes a canvas from a measurement that
# includes CSS transforms, so a figure laid out under the preview's transform is
# left with a canvas too large or too small by the preview's scale (10 to 40 per
# cent). A figure whose frame and border allowances do not quite add up to its
# width can be a few per cent out at any size; that is not what this looks for.
_CANVAS_MISFIT = r"""() => {
  const deep = (root, pred, out = []) => {
    for (const e of root.querySelectorAll('*')) {
      if (pred(e)) out.push(e);
      if (e.shadowRoot) deep(e.shadowRoot, pred, out);
    }
    return out;
  };
  const bar = deep(document, e => e.classList && e.classList.contains('hsplitter'))
    .find(e => e.getBoundingClientRect().height > 0);
  const block = bar.getRootNode().host.previousElementSibling;
  let worst = 0;
  for (const fig of deep(block.shadowRoot, e => e.classList && e.classList.contains('bk-Figure'))) {
    const canvas = deep(fig.shadowRoot || fig, e => e.classList && e.classList.contains('bk-Canvas'))[0];
    if (canvas && fig.offsetWidth) worst = Math.max(worst, Math.abs(canvas.offsetWidth / fig.offsetWidth - 1));
  }
  return worst;
}"""


def drag_plot_handle(page, dy: float, settle: float = 3.0) -> dict | None:
    """Drag the handle under the plots by ``dy`` pixels and follow the hand-over frame by frame.

    Returns the handle's position when released (``dropped``) and when the
    resize is over (``final``), the figures' height before and after, and
    ``drift``: the furthest the handle strayed from ``final`` at any drawn
    frame after release. A smooth resize leaves the handle where it was let go,
    so ``drift`` is a pixel or two at most. ``misfit`` is the largest relative
    difference in width between a figure and its canvas once settled: a few
    hundredths at most when every figure is drawn to its own size. None if
    there is no handle.
    """
    start = page.evaluate(_WATCH_PLOT_HANDLE)
    if start is None:
        return None
    time.sleep(0.2)
    page.mouse.move(start["x"], start["y"])
    page.mouse.down()
    for k in range(1, 21):
        page.mouse.move(start["x"], start["y"] + dy * k / 20)
        time.sleep(0.02)
    time.sleep(0.1)
    released = page.evaluate("() => window.__plotHandleLog.length")
    page.mouse.up()
    time.sleep(settle)
    log = page.evaluate("() => { const log = window.__plotHandleLog; window.__plotHandleLog = null; return log; }")
    before, dropped, after = log[0], log[released - 1], log[released:]
    final = after[-1]
    return {"dropped": dropped["bar"], "final": final["bar"],
            "height_before": before["height"], "height_after": final["height"],
            "drift": max(abs(e["bar"] - final["bar"]) for e in after),
            "misfit": page.evaluate(_CANVAS_MISFIT)}

"""
Browser-level checks shared by the applications' Playwright suites (``ui_test.py``).

Nothing here imports Playwright: each function takes the suite's ``page``.
"""
from __future__ import annotations

import time

# Every animation frame, after it has been drawn, record where the plot handle
# and its guide bar are, and how tall the figures above it are on screen. (A message posted from
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
    const guide = document.querySelector('.hsplitter-guide');
    window.__plotHandleLog.push({bar: bar.getBoundingClientRect().top, height: bottom - top,
                                 guide: guide ? guide.getBoundingClientRect().top : null});
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
# ratio of their widths from 1: a figure resized but not laid out again keeps a
# canvas for its old size (10 to 40 per cent out). A figure whose frame and
# border allowances do not quite add up to its width can be a few per cent out
# at any size; that is not what this looks for.
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
    """Drag the handle under the plots by ``dy`` pixels and follow the resize frame by frame.

    During the drag only the guide bar should move; on release the figures take
    their new size at once and the handle lands where the guide was let go.
    Returns the guide's position at release (``dropped``) and the handle's once
    the resize is over (``final``), the figures' height before and after,
    ``moved``: the most the figures changed height during the drag (0 when they
    stood still), ``sizes``: how many different heights the figures were shown
    at after release (1 when they jumped straight to the new size) and
    ``misfit``: the largest relative difference in width between a figure and
    its canvas once settled (a few hundredths at most when every figure is
    drawn to its own size). None if there is no handle.
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
    before, during, after = log[0], log[:released], log[released:]
    final = after[-1]
    shown = [e for e in after if e["guide"] is None]
    return {"dropped": during[-1]["guide"] if during[-1]["guide"] is not None else during[-1]["bar"],
            "final": final["bar"],
            "height_before": before["height"], "height_after": final["height"],
            "moved": max(abs(e["height"] - before["height"]) for e in during),
            "sizes": len({round(e["height"]) for e in shown if abs(e["height"] - before["height"]) > 1}),
            "misfit": page.evaluate(_CANVAS_MISFIT)}



# where each panel of a TileCanvas is: {title: {x, y, w, h (pixels, on screen), body: {w, h}}}, plus the dividers
_TILES = r"""() => {
  const deep = (root, sel, out = []) => {
    out.push(...root.querySelectorAll(sel));
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) deep(e.shadowRoot, sel, out);
    return out;
  };
  const tiles = {}, dividers = [];
  for (const tile of deep(document, '.tile')) {
    const r = tile.getBoundingClientRect();
    if (r.width === 0) continue;
    const head = tile.querySelector('.tile-head'), body = tile.querySelector('.tile-body');
    tiles[head.textContent.replace('⠿', '').trim()] = {x: r.left, y: r.top, w: r.width, h: r.height,
      head: {x: r.left + 40, y: head.getBoundingClientRect().top + 12}, body: {w: body.clientWidth, h: body.clientHeight}};
  }
  for (const d of deep(document, '.divider')) {
    const r = d.getBoundingClientRect();
    if (r.width > 0) dividers.push({x: r.left + r.width / 2, y: r.top + r.height / 2, row: d.classList.contains('row')});
  }
  const root = deep(document, '.tiles').find(e => e.getBoundingClientRect().width > 0);
  const box = root && root.getBoundingClientRect();
  return {tiles, dividers, canvas: box && {x: box.left, y: box.top, w: box.width, h: box.height}};
}"""


def tiles(page) -> dict:
    """The TileCanvas on show: its panels (screen boxes, body sizes), dividers, and its own box."""
    return page.evaluate(_TILES)


def drop_tile(page, title: str, target: str, zone: str, settle: float = 2.0) -> dict:
    """Drag a panel by its title onto ``zone`` ("swap", "left", "right", "top", "bottom") of ``target``.

    The pointer moves in small steps, as a hand does. Returns the canvas afterwards.
    """
    now = tiles(page)["tiles"]
    src, dst = now[title], now[target]
    u, v = {"swap": (0.5, 0.5), "left": (0.1, 0.5), "right": (0.9, 0.5),
            "top": (0.5, 0.1), "bottom": (0.5, 0.9)}[zone]
    page.mouse.move(src["head"]["x"], src["head"]["y"])
    page.mouse.down()
    page.mouse.move(dst["x"] + u * dst["w"], dst["y"] + v * dst["h"], steps=20)
    page.mouse.up()
    time.sleep(settle)
    return tiles(page)


def drag_divider(page, index: int, delta: float, settle: float = 2.0) -> dict:
    """Drag the ``index``-th divider by ``delta`` pixels across it; returns the canvas afterwards."""
    d = tiles(page)["dividers"][index]
    page.mouse.move(d["x"], d["y"])
    page.mouse.down()
    page.mouse.move(d["x"] + (delta if d["row"] else 0), d["y"] + (0 if d["row"] else delta), steps=12)
    page.mouse.up()
    time.sleep(settle)
    return tiles(page)

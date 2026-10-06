"""
The custom components these applications need beyond Panel's own widgets.

Each is a small ``JSComponent``: a slice of browser behaviour that Panel has no
widget for, kept here because it is about the application's *frame* rather than
about any one science — dragging the boundary between the panels, resizing the
plots, landing a batch of changes in one layout pass, and hearing the keys an
analyst presses while working.
"""
from __future__ import annotations

import weakref
from contextlib import contextmanager
from typing import Optional

import panel as pn
import param
from panel.custom import Children, JSComponent

from . import tiling


class Splitter(JSComponent):
    """A vertical drag handle that moves the boundary between the side panel and the main pane.

    A drag resizes the side panel *and* the row that wraps it, so that the main
    pane beside it — the flexible item of the layout — gives up or takes back
    exactly the width the panel gained or lost.

    Everything in both panes — Bokeh figures, Tabulator tables, the step
    logger — re-lays itself out whenever its width changes, and together
    that costs tens of milliseconds a frame: resizing live made the drag
    lag behind the cursor. So the drag moves a guide bar only (free), and
    the panels take the new width once, on release — the same scheme as
    :class:`HeightSplitter`.

    The side panel may be dragged as wide as the window allows minus
    ``main_min``; the main pane scrolls sideways when it is squeezed below
    what its content wants, rather than forbidding the drag.
    """

    # (not min_width/max_width: those are Panel's own layout parameters of the handle itself)
    panel_min = param.Integer(default=320, doc="smallest width the side panel may be dragged to")
    panel_max = param.Integer(default=1100, doc="largest width the side panel may be dragged to")
    panel_default = param.Integer(default=450, doc="width restored by a double click")
    main_min = param.Integer(default=360, doc="width the main pane always keeps (it scrolls sideways below "
                                              "what its content wants)")
    width_px = param.Integer(default=450, doc="width of the panel after the last drag")

    _esm = """
    export function render({ model, el }) {
      const bar = document.createElement('div');
      bar.className = 'splitter';
      bar.title = 'drag to move the boundary between the panels · double click resets';
      const host = () => el.getRootNode().host || el;
      const target = () => host().previousElementSibling;   // the side panel
      // the row holding panel + handle. Bokeh renders each model into a shadow root,
      // so the handle's parent is that root, not an element: parentElement is null and
      // only the shadow host leads on up the layout (previousElementSibling, in
      // contrast, resolves inside the root and needs no such step)
      const wrapper = () => { const h = host(), p = h.parentNode;
                              return h.parentElement || (p && p.host) || null; };
      let startX = 0, startW = 0, handleW = 14, minW = 0, maxW = 0, pending = null, frame = null, guide = null;
      const apply = (w) => {
        const t = target(), wrap = wrapper();
        if (!t) return;
        const px = w + 'px';
        t.style.width = px; t.style.minWidth = px; t.style.maxWidth = px;
        // the wrapper is a rigid flex item (flex: 0 0 <width>); unless it grows with
        // the panel the main pane keeps its place and the panel just overlaps it
        if (wrap) {
          const total = (w + handleW) + 'px';
          wrap.style.flex = '0 0 ' + total;
          wrap.style.width = total; wrap.style.minWidth = total; wrap.style.maxWidth = total;
        }
      };
      // Measured once per drag. The panel may grow until the main pane is down to
      // main_min; the main pane's own right edge moves out with it once its content
      // cannot shrink further, so bound it by the page's (symmetric) margin too.
      const measure = () => {
        const t = target(), wrap = wrapper();
        handleW = host().getBoundingClientRect().width || handleW;
        const left = t ? t.getBoundingClientRect().left : 0;
        const main = wrap ? wrap.nextElementSibling : null;
        const right = Math.min(main ? main.getBoundingClientRect().right : Infinity,
                               window.innerWidth - left);
        minW = model.panel_min;
        maxW = Math.max(minW, Math.min(model.panel_max, right - left - handleW - model.main_min));
      };
      // The guide is a bar the size of the handle, fixed over the page, that stands
      // where the boundary will be; the panels themselves do not move until release.
      const showGuide = () => {
        const r = host().getBoundingClientRect();
        guide = document.createElement('div');
        guide.className = 'splitter-guide';
        Object.assign(guide.style, { position: 'fixed', top: r.top + 'px', left: r.left + 'px',
                                     width: r.width + 'px', height: r.height + 'px', zIndex: 10000,
                                     pointerEvents: 'none' });
        const line = document.createElement('div');
        Object.assign(line.style, { width: '8px', height: 'calc(100% - 8px)', margin: '4px 3px',
                                    borderRadius: '4px', background: '#1f4e9c' });
        guide.appendChild(line);
        document.body.appendChild(guide);
      };
      const onMove = (e) => {
        pending = Math.max(minW, Math.min(maxW, startW + (e.clientX - startX)));
        if (frame === null) frame = requestAnimationFrame(() => {
          frame = null;
          if (guide) guide.style.transform = 'translateX(' + (pending - startW) + 'px)';
        });
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = ''; document.body.style.userSelect = '';
        bar.classList.remove('dragging');
        if (frame !== null) { cancelAnimationFrame(frame); frame = null; }
        if (guide) { guide.remove(); guide = null; }
        if (pending !== null) { apply(pending); model.width_px = Math.round(pending); pending = null; }
      };
      bar.addEventListener('mousedown', (e) => {
        const t = target();
        if (!t || e.button !== 0) return;
        startX = e.clientX; startW = t.getBoundingClientRect().width;
        measure();
        showGuide();
        bar.classList.add('dragging');
        document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
        e.preventDefault();
      });
      bar.addEventListener('dblclick', () => { measure(); apply(model.width_px = model.panel_default); });
      return bar;
    }
    """

    _stylesheets = ["""
    :host { display: flex; align-self: stretch; width: 14px !important; min-width: 14px; max-width: 14px; }
    .splitter { width: 8px; min-height: 100%; cursor: col-resize; background: #e5e7eb; border-radius: 4px;
                margin: 4px 3px; transition: background .15s; }
    .splitter:hover { background: #9aa1ab; }
    .splitter.dragging { background: #c7d2e5; }
    """]


class HeightSplitter(JSComponent):
    """A horizontal drag handle under a block of figures that sets how large they are drawn.

    Place it directly after the block in a column. It reports a single number,
    ``value`` (the application decides what it means: the Zijderveld frame in
    Directions, the Arai frame in Intensity), and the application resizes its
    figures from it in Python, since their geometry is tied together there.

    Re-laying out Bokeh figures is far too slow to follow a cursor, so, as
    with :class:`Splitter`, the drag moves a guide bar only and the figures
    are resized once, on release. The guide stands where the handle will be
    once they are: ``px_per_value`` (block height gained per unit of
    ``value``) converts the distance dragged into a value. The owner lands
    the resize with :class:`LayoutHold`, so its many size changes cost the
    browser one layout pass.

    (An earlier version scaled the block with a CSS transform during the drag
    and kept the preview on until the resized figures arrived. It was
    smoother to look at, but a transform cannot preview the side column, so
    the two handles behaved differently; and Bokeh measures its views through
    a transform, which took a hand-made re-layout to undo.)

    Given ``width_per_value`` (how much wider the figures get per unit of
    value), the figures may not be dragged wider than the block: a block that
    wraps (a flex box) would otherwise drop half its figures below the rest on
    release, far from where the guide was let go.
    """

    value = param.Integer(default=430, doc="the size the application draws its figures at")
    default_value = param.Integer(default=430, doc="value restored by a double click")
    minimum = param.Integer(default=240, doc="smallest value the handle may be dragged to")
    maximum = param.Integer(default=1000, doc="largest value the handle may be dragged to")
    px_per_value = param.Number(default=1.0, bounds=(0.05, None),
                                doc="height the block gains per unit of value (updated by the application)")
    width_per_value = param.Number(default=None, allow_None=True, bounds=(0.05, None),
                                   doc="width the figures gain per unit of value; if given, they are kept "
                                       "within the block's width (updated by the application)")

    _esm = """
    export function render({ model, el }) {
      const bar = document.createElement('div');
      bar.className = 'hsplitter';
      bar.title = 'drag to resize the plots · double click to reset';
      const host = () => el.getRootNode().host || el;
      const block = () => host().previousElementSibling;      // the figures above the handle
      // The right edge of the figures, measured from the block's left: they are
      // found however deep the layout nests them (each model has its own shadow root)
      const figuresWidth = () => {
        const b = block();
        if (!b) return 0;
        const left = b.getBoundingClientRect().left;
        let w = 0;
        const walk = (root) => {
          for (const e of root.querySelectorAll('*')) {
            if (e.classList.contains('bk-Figure')) w = Math.max(w, e.getBoundingClientRect().right - left);
            else if (e.shadowRoot) walk(e.shadowRoot);
          }
        };
        if (b.shadowRoot) walk(b.shadowRoot);
        return w;
      };
      const clamp = (v) => Math.max(model.minimum, Math.min(model.maximum, v));

      // v0: the value when the drag started; vmax: the largest value that keeps the
      // figures within the block's width (width_per_value)
      let startY = 0, v0 = 0, vmax = Infinity, pending = null, frame = null, guide = null;
      // the guide is a bar the shape of the handle, fixed over the page, standing
      // where the handle will be once the figures take the new size
      const showGuide = () => {
        const r = bar.getBoundingClientRect();
        guide = document.createElement('div');
        guide.className = 'hsplitter-guide';
        Object.assign(guide.style, { position: 'fixed', top: r.top + 'px', left: r.left + 'px',
                                     width: r.width + 'px', height: r.height + 'px', borderRadius: '4px',
                                     background: '#1f4e9c', zIndex: 10000, pointerEvents: 'none' });
        document.body.appendChild(guide);
      };
      const onMove = (e) => {
        pending = Math.min(vmax, clamp(v0 + (e.clientY - startY) / model.px_per_value));
        if (frame === null) frame = requestAnimationFrame(() => {
          frame = null;
          if (guide) guide.style.transform = 'translateY(' + ((pending - v0) * model.px_per_value) + 'px)';
        });
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = ''; document.body.style.userSelect = '';
        bar.classList.remove('dragging');
        if (frame !== null) { cancelAnimationFrame(frame); frame = null; }
        if (guide) { guide.remove(); guide = null; }
        if (pending !== null) model.value = Math.round(pending);
        pending = null;
      };
      bar.addEventListener('mousedown', (e) => {
        if (!block() || e.button !== 0) return;
        startY = e.clientY; v0 = model.value;
        // (12 px in hand: the figures' containers, a grid with its gaps, are a
        // little wider than the figures, and the application rounds its sizes)
        const w = figuresWidth();
        vmax = model.width_per_value && w > 0
          ? Math.max(v0, Math.floor(v0 + (block().clientWidth - 12 - w) / model.width_per_value))
          : Infinity;
        showGuide();
        bar.classList.add('dragging');
        document.body.style.cursor = 'row-resize'; document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
        e.preventDefault();
      });
      bar.addEventListener('dblclick', () => { model.value = model.default_value; });
      return bar;
    }
    """

    _stylesheets = ["""
    :host { display: block; width: 100%; }
    .hsplitter { height: 8px; cursor: row-resize; background: #e5e7eb; border-radius: 4px;
                 margin: 2px 0; transition: background .15s; }
    .hsplitter:hover { background: #9aa1ab; }
    .hsplitter.dragging { background: #c7d2e5; }
    """]


class LayoutHold(JSComponent):
    """Invisible component that lands a batch of changes in one layout pass of the browser.

    BokehJS lays the whole page out again — synchronously — for every property
    that affects layout: a width or height, ``visible``, ``css_classes``. A
    callback that hides three widgets and resizes a table pays four layouts, at
    some 20 ms each for a page like Directions'; the ten size changes of its
    plot-height handle paid ten, visibly in two passes. Wrap such a callback::

        with LayoutHold.batch():
            self.planes_box.visible = bool(planes)
            self.table.height = ...

    and its changes travel as *one* message, bracketed by ``begin`` and
    ``end``; the browser notes the layout requests between the two and honours
    them once, when ``end`` is applied. The single message matters: without
    ``pn.io.hold()`` Panel writes each change as its own message, and its own
    model updates before Bokeh's, so nothing could bracket them. (A batch is
    applied in one task; should ``end`` not be in the message after all, the
    hold releases itself at the end of that task — the page is never left
    unlaid.)

    One instance per session, mounted by the shell's ``Workspace``;
    :meth:`batch` finds it by the current document, and outside a server
    session (a test, a notebook) does nothing but run the body.
    """

    begin = param.Integer(default=0, doc="bumped first in a batch: layout requests are collected from here")
    end = param.Integer(default=0, doc="bumped last in a batch: the collected requests are honoured, once")

    _by_document: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
    _without_document: Optional["LayoutHold"] = None

    def __init__(self, **params):
        super().__init__(**params)
        self._depth = 0

    @classmethod
    def of_session(cls) -> "LayoutHold":
        """The session's instance (made on first use; the shell mounts it)."""
        doc = pn.state.curdoc
        if doc is None:
            if cls._without_document is None:
                cls._without_document = cls(width=0, height=0, margin=0)
            return cls._without_document
        hold = cls._by_document.get(doc)
        if hold is None:
            hold = cls._by_document[doc] = cls(width=0, height=0, margin=0)
        return hold

    @classmethod
    @contextmanager
    def batch(cls):
        """Run the body so that the browser lays the page out once for all its changes."""
        hold = cls.of_session()
        with pn.io.hold():
            hold._depth += 1
            if hold._depth == 1:
                hold.begin += 1
            try:
                yield
            finally:
                hold._depth -= 1
                if hold._depth == 0:
                    hold.end += 1

    _esm = """
    // While `held`, LayoutDOMView.invalidate_layout only notes the root views that
    // asked; release() lays each out once. Module scope: one hold for the page.
    let layout_dom = null;
    try { layout_dom = Bokeh.require('models/layouts/layout_dom'); } catch (e) { layout_dom = null; }
    let held = null;
    const release = () => {
      if (!held) return;
      clearTimeout(held.timer);
      layout_dom.LayoutDOMView.prototype.invalidate_layout = held.invalidate;
      const roots = held.roots;
      held = null;
      for (const root of roots) root.invalidate_layout();
    };
    const hold = () => {
      if (!layout_dom || held) return;
      const proto = layout_dom.LayoutDOMView.prototype, roots = new Set();
      // a batch is applied within one task: the timer only fires if `end` was not in it
      held = { invalidate: proto.invalidate_layout, roots, timer: setTimeout(release, 0) };
      proto.invalidate_layout = function () {    // what the original does, minus the layout itself
        let view = this;
        while (view.parent instanceof layout_dom.LayoutDOMView) view = view.parent;
        roots.add(view);
      };
    };

    export function render({ model }) {
      model.on('begin', hold);
      model.on('end', release);
      return document.createElement('span');
    }
    """


class Hotkeys(JSComponent):
    """Invisible component forwarding key presses to Python (not while typing in a field).

    ``keys`` names the ones it takes; by default the arrows (← → specimens,
    ↑ ↓ the selected row) and [ ] { } (fit bounds).
    """

    keys = param.List(default=["ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown", "[", "]", "{", "}"],
                      doc="the key values (KeyboardEvent.key) forwarded; the browser's own handling is suppressed")
    key = param.String(default="")
    n = param.Integer(default=0, doc="incremented on every accepted key press")

    _esm = """
    export function render({ model }) {
      const el = document.createElement('span');
      const editing = (e) => {
        const t = (e.composedPath && e.composedPath()[0]) || e.target;
        const tag = t && t.tagName;
        return ['INPUT', 'SELECT', 'TEXTAREA'].includes(tag) || (t && t.isContentEditable);
      };
      document.addEventListener('keydown', (e) => {
        if (editing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
        if (model.keys.includes(e.key)) {
          e.preventDefault();
          model.key = e.key;
          model.n = model.n + 1;
        }
      });
      return el;
    }
    """



class TileCanvas(JSComponent):
    """Panels tiled over a fixed area, as a tiling window manager tiles windows.

    The panels always fill the canvas exactly -- no gaps, no overlaps, nothing
    pushed out over what lies below -- and are rearranged by dragging:

    * a panel's title bar dropped on the middle of another panel swaps the two;
    * dropped near another panel's edge, the panel moves to that side of it
      (the other panel gives up half its area, the panel's old place goes to
      its neighbour);
    * the gap between two panels is a divider: drag it to share the space
      differently.

    During a drag only an outline moves; on release the layout is recomputed
    in Python (:mod:`pmagpy_panel.tiling`) and the panels and the figures in
    them are resized once (see :class:`LayoutHold`). The canvas's height is
    the application's (``height``); its width is the browser's, reported as
    ``width_px``. ``sizes`` holds the pixel size of every panel's body after the
    last layout, for the application to fit its fixed-size figures to.

    A panel is any Panel object; its ``name`` is its title. ``tree`` is the
    layout (see :mod:`~pmagpy_panel.tiling`), JSON to save and restore.
    """

    objects = Children(doc="the panels; each one's name is its title")
    titles = param.List(default=[], doc="the panels' titles, in the order of objects")
    rects = param.List(default=[], doc="{x, y, w, h} of each panel (pixels), in the order of objects")
    dividers = param.List(default=[], doc="the dividers between panels (see tiling.layout)")
    width_px = param.Integer(default=0, doc="the canvas's width in the browser")
    drop = param.Dict(default={}, doc="the last panel dropped: {src, dst, zone, n}")
    split = param.Dict(default={}, doc="the last divider dropped: {path, ratio, n}")
    sizes = param.Dict(default={}, doc="{title: (width, height)} of each panel's body after the last layout")
    gap = param.Integer(default=8, doc="the space between panels, which is also the divider")
    min_panel = param.Integer(default=140, doc="smallest width or height a divider leaves a panel")

    HEAD = 26        # a panel's title bar, border included

    _esm = """
    export function render({ model, el, view }) {
      const root = document.createElement('div');
      root.className = 'tiles';
      const tiles = [];
      const mount = () => {
        const kids = model.get_child('objects');
        kids.forEach((child, i) => {
          let tile = tiles[i];
          if (!tile) {
            tile = document.createElement('div'); tile.className = 'tile';
            const head = document.createElement('div'); head.className = 'tile-head';
            head.title = 'drag onto another panel: its middle swaps the two, its edge puts this panel on that side';
            const body = document.createElement('div'); body.className = 'tile-body';
            tile.append(head, body); root.appendChild(tile); tiles[i] = tile;
            head.addEventListener('mousedown', (e) => startMove(e, i));
          }
          tile.querySelector('.tile-head').innerHTML = '<span class="grip">⠿</span>' + (model.titles[i] || '');
          const body = tile.querySelector('.tile-body');
          if (child && child.parentNode !== body) { body.innerHTML = ''; body.appendChild(child); }
        });
      };
      const place = () => {
        model.rects.forEach((r, i) => {
          if (!tiles[i]) return;
          Object.assign(tiles[i].style, {left: r.x + 'px', top: r.y + 'px', width: r.w + 'px', height: r.h + 'px',
                                         visibility: 'visible'});
        });
        for (const d of root.querySelectorAll('.divider')) d.remove();
        for (const d of model.dividers) {
          const bar = document.createElement('div');
          bar.className = 'divider ' + d.orient;
          Object.assign(bar.style, {left: d.x + 'px', top: d.y + 'px', width: d.w + 'px', height: d.h + 'px'});
          bar.title = 'drag to share the space between the panels differently';
          bar.addEventListener('mousedown', (e) => startResize(e, d));
          root.appendChild(bar);
        }
      };
      // --- moving a panel: an outline of where it would go, the layout on release
      const local = (e) => { const r = root.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
      const zoneOf = (x, y, r) => {
        const u = (x - r.x) / r.w, v = (y - r.y) / r.h;
        if (u > 0.3 && u < 0.7 && v > 0.3 && v < 0.7) return 'swap';
        const near = {left: u, right: 1 - u, top: v, bottom: 1 - v};
        return Object.keys(near).reduce((a, b) => near[a] <= near[b] ? a : b);
      };
      const preview = (r, zone) => {
        if (zone === 'swap') return r;
        const half = {left: {x: r.x, y: r.y, w: r.w / 2, h: r.h}, right: {x: r.x + r.w / 2, y: r.y, w: r.w / 2, h: r.h},
                      top: {x: r.x, y: r.y, w: r.w, h: r.h / 2}, bottom: {x: r.x, y: r.y + r.h / 2, w: r.w, h: r.h / 2}};
        return half[zone];
      };
      const startMove = (e, src) => {
        if (e.button !== 0) return;
        e.preventDefault();
        const ghost = document.createElement('div'); ghost.className = 'drop-preview'; ghost.style.display = 'none';
        root.appendChild(ghost);
        tiles[src].classList.add('lifted');
        let target = null, zone = null;
        const onMove = (ev) => {
          const [x, y] = local(ev);
          target = null;
          model.rects.forEach((r, j) => { if (j !== src && x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) target = j; });
          if (target === null) { ghost.style.display = 'none'; return; }
          zone = zoneOf(x, y, model.rects[target]);
          const p = preview(model.rects[target], zone);
          Object.assign(ghost.style, {display: 'block', left: p.x + 'px', top: p.y + 'px', width: p.w + 'px', height: p.h + 'px'});
          ghost.textContent = zone === 'swap' ? 'swap with ' + model.titles[target] : '';
        };
        const onUp = () => {
          document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp);
          document.body.style.cursor = ''; document.body.style.userSelect = '';
          ghost.remove(); tiles[src].classList.remove('lifted');
          if (target !== null)
            model.drop = {src: model.titles[src], dst: model.titles[target], zone: zone, n: Date.now()};
        };
        document.body.style.cursor = 'grabbing'; document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp);
      };
      // --- moving a divider: a guide bar, the new ratio on release
      const startResize = (e, d) => {
        if (e.button !== 0) return;
        e.preventDefault();
        const row = d.orient === 'row', gap = model.gap, lo = d.start + model.min_panel,
              hi = d.start + d.length - gap - model.min_panel;
        const guide = document.createElement('div'); guide.className = 'divider-guide ' + d.orient;
        Object.assign(guide.style, {left: d.x + 'px', top: d.y + 'px', width: d.w + 'px', height: d.h + 'px'});
        root.appendChild(guide);
        let pos = row ? d.x : d.y;
        const onMove = (ev) => {
          const [x, y] = local(ev);
          pos = Math.max(lo, Math.min(hi, (row ? x : y) - gap / 2));
          guide.style[row ? 'left' : 'top'] = pos + 'px';
        };
        const onUp = () => {
          document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp);
          document.body.style.cursor = ''; document.body.style.userSelect = '';
          guide.remove();
          model.split = {path: d.path, ratio: (pos - d.start) / (d.length - gap), n: Date.now()};
        };
        document.body.style.cursor = row ? 'col-resize' : 'row-resize'; document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp);
      };
      // The width is the browser's: reported whenever it changes (the window, the side
      // column's handle, the tab coming into view). A tab not on show has no size, and
      // Bokeh lays its figures out at that size; shown again at the size they had, they
      // are not measured again -- so coming into view, the canvas asks for a layout.
      let timer = null, shown = false;
      const observer = new ResizeObserver(() => {
        const visible = root.offsetWidth > 0 && root.offsetHeight > 0;
        if (visible && !shown) view.invalidate_layout();
        shown = visible;
        // the first width at once (the panels are hidden until they have a place), later ones once settled
        const report = () => { if (root.offsetWidth > 0) model.width_px = Math.round(root.clientWidth); };
        clearTimeout(timer);
        if (!model.width_px) report(); else timer = setTimeout(report, 120);
      });
      observer.observe(root);
      model.on('objects', () => { mount(); place(); });
      model.on('titles', mount);
      model.on(['rects', 'dividers'], place);
      model.on('remove', () => observer.disconnect());
      mount(); place();
      return root;
    }
    """

    _stylesheets = ["""
    :host { display: block; }
    .tiles { position: relative; width: 100%; height: 100%; }
    .tile { position: absolute; box-sizing: border-box; visibility: hidden; display: flex; flex-direction: column; overflow: hidden;
            background: #ffffff; border: 1px solid #e3e6eb; border-radius: 8px; box-shadow: 0 1px 2px rgba(16, 24, 40, .06);
            transition: left .16s ease, top .16s ease, width .16s ease, height .16s ease, opacity .12s; }
    .tile.lifted { opacity: .55; }
    .tile-head { flex: 0 0 25px; box-sizing: border-box; display: flex; align-items: center; gap: 6px; padding: 0 10px;
                 font-weight: 600; font-size: 0.72rem; letter-spacing: .05em; text-transform: uppercase; color: #5b6470;
                 background: #f7f8fa; border-bottom: 1px solid #edf0f3; cursor: grab; user-select: none;
                 white-space: nowrap; overflow: hidden; }
    .tile-head:hover { background: #eef3fb; color: #1f2937; }
    .tile-head .grip { color: #b5bbc4; font-size: 0.9rem; }
    .tile-body { flex: 1 1 auto; position: relative; overflow: hidden; display: flex; justify-content: center;
                 align-items: flex-start; padding-top: 2px; }
    .divider { position: absolute; z-index: 2; }
    .divider.row { cursor: col-resize; }
    .divider.col { cursor: row-resize; }
    .divider::after { content: ''; position: absolute; border-radius: 3px; background: transparent; transition: background .15s; }
    .divider.row::after { left: 2px; right: 2px; top: 30%; bottom: 30%; }
    .divider.col::after { top: 2px; bottom: 2px; left: 30%; right: 30%; }
    .divider:hover::after { background: #9aa1ab; }
    .divider-guide { position: absolute; z-index: 5; pointer-events: none; }
    .divider-guide::after { content: ''; position: absolute; inset: 1px; border-radius: 3px; background: #1f4e9c; }
    .drop-preview { position: absolute; z-index: 4; pointer-events: none; box-sizing: border-box; border-radius: 8px;
                    border: 2px dashed #1f4e9c; background: rgba(31, 78, 156, .10); display: flex;
                    align-items: center; justify-content: center; font: 600 0.8rem sans-serif; color: #1f4e9c; }
    """]

    def __init__(self, objects=(), tree=None, **params):
        objects = list(objects)
        params.setdefault("titles", [obj.name for obj in objects])
        super().__init__(objects=objects, **params)
        self._tree = tree if tree is not None and tiling.valid(tree, self.titles) else self._default_tree()
        self.param.watch(self._on_drop, "drop")
        self.param.watch(self._on_split, "split")
        self.param.watch(lambda e: self._relayout(), ["width_px", "height", "gap"])
        self._relayout()

    def _default_tree(self):
        tree = self.titles[-1]
        for title in reversed(self.titles[:-1]):
            tree = ["row", 0.5, title, tree]
        return tree

    @property
    def tree(self):
        """The layout (see :mod:`pmagpy_panel.tiling`)."""
        return self._tree

    def arrange(self, tree) -> None:
        """Lay the panels out as ``tree`` (ignored unless it holds exactly these panels)."""
        if tiling.valid(tree, self.titles):
            self._tree = tree
            self._relayout()

    def _on_drop(self, event):
        drop = event.new or {}
        src, dst, zone = drop.get("src"), drop.get("dst"), drop.get("zone")
        if src not in self.titles or dst not in self.titles or src == dst:
            return
        self.arrange(tiling.swap(self._tree, src, dst) if zone == "swap" else tiling.move(self._tree, src, dst, zone))

    def _on_split(self, event):
        move = event.new or {}
        path = move.get("path")
        if path is None:
            return
        node = tiling.node_at(self._tree, path)
        if tiling.is_leaf(node):
            return
        # the split's extent along its axis, so that no panel is left narrower than min_panel
        extent = next((d["length"] for d in self.dividers if list(d["path"]) == list(path)), 0) or 1
        self.arrange(tiling.set_ratio(self._tree, path, move.get("ratio", node[1]),
                                      minimum=self.min_panel / max(extent - self.gap, 1)))

    def _relayout(self):
        """Place the panels for the current tree and size, in one layout pass."""
        width, height = self.width_px, self.height or 0
        if not (width > 0 and height > 0):
            return
        # a panel dropped into a small corner takes its room from the larger ones around it
        self._tree = tiling.fit_minimum(self._tree, width, height, self.min_panel, self.gap)
        rects, dividers = tiling.layout(self._tree, width, height, self.gap)
        with LayoutHold.batch():
            self.rects = [dict(zip("xywh", rects[t])) for t in self.titles]
            self.dividers = dividers
            self.sizes = {t: (rects[t][2] - 2, rects[t][3] - self.HEAD - 2) for t in self.titles}

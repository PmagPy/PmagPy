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
from panel.custom import JSComponent


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

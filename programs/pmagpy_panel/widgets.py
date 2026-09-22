"""
The custom components these applications need beyond Panel's own widgets.

Each is a small ``JSComponent``: a slice of browser behaviour that Panel has no
widget for, kept here because it is about the application's *frame* rather than
about any one science — dragging the boundary between the panels, resizing the
plots, and hearing the keys an analyst presses while working.
"""
from __future__ import annotations

import param
from panel.custom import JSComponent


class Splitter(JSComponent):
    """A vertical drag handle that moves the boundary between the side panel and the main pane.

    A drag resizes the side panel *and* the row that wraps it, so that the main
    pane beside it — the flexible item of the layout — gives up or takes back
    exactly the width the panel gained or lost.
    """

    # (not min_width/max_width: those are Panel's own layout parameters of the handle itself)
    panel_min = param.Integer(default=320, doc="smallest width the side panel may be dragged to")
    panel_max = param.Integer(default=1100, doc="largest width the side panel may be dragged to")
    panel_default = param.Integer(default=450, doc="width restored by a double click")
    main_min = param.Integer(default=880, doc="width the main pane keeps: the plots and fit controls stay whole")
    width_px = param.Integer(default=450, doc="width of the panel after the last drag")

    _esm = """
    export function render({ model, el }) {
      const bar = document.createElement('div');
      bar.className = 'splitter';
      bar.title = 'drag to move the boundary between the panels';
      const host = () => el.getRootNode().host || el;
      const target = () => host().previousElementSibling;   // the side panel
      // the row holding panel + handle. Bokeh renders each model into a shadow root,
      // so the handle's parent is that root, not an element: parentElement is null and
      // only the shadow host leads on up the layout (previousElementSibling, in
      // contrast, resolves inside the root and needs no such step)
      const wrapper = () => { const h = host(), p = h.parentNode;
                              return h.parentElement || (p && p.host) || null; };
      let startX = 0, startW = 0, handleW = 14, minW = 0, maxW = 0, pending = null, frame = null;
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
      // Measured once per drag: reading layout on every mouse move (and so forcing a
      // synchronous reflow before each frame) is what makes a resize feel heavy.
      // The panel may not grow so far that the plots of the main pane are squeezed
      // out; the main pane's own right edge moves out with it once its content
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
      // The panels follow the cursor, at most one resize per animation frame however
      // fast the mouse reports; the move handler itself only does arithmetic.
      const onMove = (e) => {
        pending = Math.max(minW, Math.min(maxW, startW + (e.clientX - startX)));
        if (frame === null) frame = requestAnimationFrame(() => { frame = null; apply(pending); });
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = ''; document.body.style.userSelect = '';
        bar.classList.remove('dragging');
        if (frame !== null) { cancelAnimationFrame(frame); frame = null; }
        if (pending !== null) { apply(pending); model.width_px = Math.round(pending); pending = null; }
      };
      bar.addEventListener('mousedown', (e) => {
        const t = target();
        if (!t) return;
        startX = e.clientX; startW = t.getBoundingClientRect().width;
        measure();
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
    .splitter:hover, .splitter.dragging { background: #9aa1ab; }
    .splitter.dragging { background: #1f4e9c; }
    """]


class HeightSplitter(JSComponent):
    """A horizontal drag handle under a block of figures that sets how large they are drawn.

    Place it directly after the block in a column. It reports a single number,
    ``value`` (the application decides what it means: the Zijderveld frame in
    Directions, the Arai frame in Intensity), and the application resizes its
    figures from it in Python, since their geometry is tied together there.

    Re-laying out Bokeh figures costs about 100 ms, far too slow to follow a
    cursor. So the drag scales the block with a CSS transform, which is free
    and immediate, and the real resize happens once, on release. How the two
    are joined is what makes the resize feel smooth:

    * during the drag the block's bottom edge follows the cursor, so the handle
      stays under it; ``px_per_value`` (block height gained per unit of
      ``value``) converts that height into a value;
    * after release the preview stays on until the resized figures arrive, so
      the plots never fall back to their size before the drag;
    * when they arrive, the transform comes off and Bokeh is asked to lay the
      block out again. Bokeh measures its views with getBoundingClientRect,
      which includes a transform, and measures again only when a view's box
      changes size, which removing a transform does not do: without this a
      figure laid out under the preview keeps a canvas sized for the scaled
      box, and is drawn too large or too small from then on;
    * whatever small difference is left between the preview and the real
      layout (a uniform scale cannot follow axes and legends, which do not
      grow with the frame) is eased out with a transform alone, so nothing is
      laid out, or measured, while it runs.

    Given ``width_per_value`` (how much wider the figures get per unit of
    value), the figures may not be dragged wider than the block: a block that
    wraps (a flex box) would otherwise drop half its figures below the rest on
    release, a jump far from where the handle was let go.
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
      // The figures' laid-out extent, measured from the block's top left corner.
      // They are found however deep the layout nests them, and the scale the
      // preview has put on the block is divided out, so this is the size the
      // figures really have, even mid-preview and however a flex box has wrapped them.
      let scale = 1;
      const figures = () => {
        const out = [], walk = (root) => {
          for (const e of root.querySelectorAll('*')) {
            if (e.classList.contains('bk-Figure')) out.push(e);
            else if (e.shadowRoot) walk(e.shadowRoot);
          }
        };
        const b = block();
        if (b && b.shadowRoot) walk(b.shadowRoot);
        return out;
      };
      const extent = () => {
        const b = block();
        if (!b) return {w: 0, h: 0};
        const origin = b.getBoundingClientRect();
        let w = 0, h = 0;
        for (const f of figures()) {
          const r = f.getBoundingClientRect();
          w = Math.max(w, r.right - origin.left); h = Math.max(h, r.bottom - origin.top);
        }
        return {w: w / scale, h: h / scale};
      };
      const clamp = (v) => Math.max(model.minimum, Math.min(model.maximum, v));

      // v0/h0: the value and the figures' height when the drag started; below:
      // the block's own height beyond its figures (margins); vmax: the largest
      // value that keeps the figures within the block's width (width_per_value);
      // target: the height the figures are shown at
      let startY = 0, v0 = 0, h0 = 0, below = 0, vmax = Infinity, target = null, pending = null, frame = null;
      let observer = null, fallback = null, easing = null;

      const reset = () => {
        const b = block();
        if (b) for (const k of ['transform', 'transformOrigin', 'height', 'transition'])
          b.style[k] = '';
        scale = 1;
      };
      // Show the block `target` tall, whatever size its figures have reached. The
      // block's own height is set too, so that what lies below moves with it.
      const show = () => {
        const b = block(), h = extent().h;
        if (!b || !h) return;
        scale = target / h;
        b.style.transition = '';
        b.style.transformOrigin = 'top left';
        b.style.transform = 'scale(' + scale + ')';
        b.style.height = (target + below) + 'px';
      };
      const stopWatching = () => {
        if (observer) { observer.disconnect(); observer = null; }
        if (fallback !== null) { clearTimeout(fallback); fallback = null; }
      };
      // Lay the block out again, measured without a transform (see the docstring).
      const relayout = () => {
        const b = block(), B = window.Bokeh;
        if (!b || !B || !B.index || typeof B.index.query !== 'function') return;
        for (const view of B.index.query((v) => v.el === b)) { view.compute_layout(); break; }
      };
      // The figures are in: hand over to them, easing out what is left.
      const land = () => {
        stopWatching();
        const b = block(), shown = target;
        reset(); target = null;
        if (!b) return;
        relayout();
        const h = extent().h;
        if (!shown || !h || Math.abs(shown / h - 1) < 0.002) return;
        b.style.transformOrigin = 'top left';
        b.style.transform = 'scale(' + (shown / h) + ')';
        void b.offsetHeight;             // commit the start of the transition
        b.style.transition = 'transform 160ms ease-out';
        b.style.transform = 'scale(1)';
        easing = setTimeout(() => { easing = null; reset(); }, 200);
      };
      // Drop a hand-over still running (a new drag takes over from it).
      const interrupt = () => {
        const busy = target !== null || easing !== null;
        stopWatching();
        if (easing !== null) { clearTimeout(easing); easing = null; }
        reset(); target = null;
        if (busy) relayout();
      };
      // Ask for `v` and keep the block `target` tall until the figures have it.
      const commit = (v) => {
        if (v === model.value) { land(); return; }
        show();
        // a ResizeObserver reports every element once when it starts watching;
        // the figures are in when one of them has a new size
        const sizes = new Map(figures().map((f) => [f, f.offsetWidth + 'x' + f.offsetHeight]));
        observer = new ResizeObserver(() => {
          for (const [f, size] of sizes) {
            if (f.offsetWidth + 'x' + f.offsetHeight !== size) { land(); return; }
          }
        });
        for (const f of sizes.keys()) observer.observe(f);
        fallback = setTimeout(land, 2000);        // should nothing arrive, do not stay scaled
        model.value = v;
      };

      const onMove = (e) => {
        pending = Math.min(vmax, clamp(v0 + (e.clientY - startY) / model.px_per_value));
        if (frame === null) {
          frame = requestAnimationFrame(() => {
            frame = null;
            target = h0 + (pending - v0) * model.px_per_value;
            show();
          });
        }
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = ''; document.body.style.userSelect = '';
        bar.classList.remove('dragging');
        if (frame !== null) { cancelAnimationFrame(frame); frame = null; }
        const v = pending === null ? v0 : Math.min(vmax, Math.round(pending));
        pending = null;
        target = h0 + (v - v0) * model.px_per_value;
        commit(v);
      };
      bar.addEventListener('mousedown', (e) => {
        if (!block()) return;
        interrupt();
        startY = e.clientY; v0 = model.value;
        const b = block(), size = extent();
        h0 = size.h; below = Math.max(0, b.offsetHeight - size.h);
        // (12 px in hand: the figures' containers, a grid with its gaps, are a
        // little wider than the figures, and the application rounds its sizes)
        vmax = model.width_per_value && size.w > 0
          ? Math.max(v0, Math.floor(v0 + (b.clientWidth - 12 - size.w) / model.width_per_value))
          : Infinity;
        bar.classList.add('dragging');
        document.body.style.cursor = 'row-resize'; document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
        e.preventDefault();
      });
      bar.addEventListener('dblclick', () => {
        if (!block()) return;
        interrupt();
        const b = block(), h = extent().h;
        below = Math.max(0, b.offsetHeight - h);
        target = h + (model.default_value - model.value) * model.px_per_value;
        commit(model.default_value);
      });
      return bar;
    }
    """

    _stylesheets = ["""
    :host { display: block; width: 100%; }
    .hsplitter { height: 8px; cursor: row-resize; background: #e5e7eb; border-radius: 4px;
                 margin: 2px 0; transition: background .15s; }
    .hsplitter:hover, .hsplitter.dragging { background: #9aa1ab; }
    .hsplitter.dragging { background: #1f4e9c; }
    """]


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

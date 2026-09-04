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
    """A horizontal drag handle that reports the height the plots above it should take.

    The side panel's ``Splitter`` resizes DOM elements itself, but the plots are
    Bokeh figures whose geometry belongs in ``plots.py`` — the frame, the square
    net beside it and the M/M₀ strip under that are tied together — so this
    handle reports a height and Python resizes the figures.

    Re-laying out those figures costs about 100 ms whoever asks for it (the
    same in the browser as through Python), far too slow to follow a cursor.
    So the drag scales the plots with a CSS transform, which is free and
    immediate, and the real resize happens once, on release: live to the eye,
    crisp when it settles.
    """

    value = param.Integer(default=430, doc="height in pixels the plot frame should take")
    default_value = param.Integer(default=430, doc="height restored by a double click")
    minimum = param.Integer(default=240, doc="smallest the plots may be dragged to")
    maximum = param.Integer(default=1000, doc="largest the plots may be dragged to")

    _esm = """
    export function render({ model, el }) {
      const bar = document.createElement('div');
      bar.className = 'hsplitter';
      bar.title = 'drag to resize the plots · double click to reset';
      const host = () => el.getRootNode().host || el;
      const plots = () => host().previousElementSibling;       // the row of figures
      let startY = 0, startV = 0, box = null, pending = null, frame = null;
      const clamp = (v) => Math.max(model.minimum, Math.min(model.maximum, v));
      // the preview: the row is scaled where it stands, and its box is scaled with
      // it so that whatever sits below moves too and nothing overflows sideways
      const preview = (scale) => {
        const t = plots();
        if (!t || !box) return;
        t.style.transformOrigin = 'top left';
        t.style.transform = scale === null ? '' : 'scale(' + scale + ')';
        t.style.width = scale === null ? '' : (box.width * scale) + 'px';
        t.style.height = scale === null ? '' : (box.height * scale) + 'px';
      };
      const onMove = (e) => {
        pending = clamp(startV + (e.clientY - startY));
        if (frame === null) {
          // the frame takes the whole change in height, so the preview scales the
          // row by the ratio that moves its bottom edge exactly that far: the
          // handle stays under the cursor and lands where the resize will put it.
          // (A uniform scale stretches the legend and toolbar strip too, which the
          // resize leaves alone, so the width is a few per cent out mid-drag.)
          frame = requestAnimationFrame(() => {
            frame = null;
            preview((box.height + (pending - startV)) / box.height);
          });
        }
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = ''; document.body.style.userSelect = '';
        bar.classList.remove('dragging');
        if (frame !== null) { cancelAnimationFrame(frame); frame = null; }
        preview(null);               // hand the size over to the real figures
        if (pending !== null) model.value = Math.round(pending);
        pending = null; box = null;
      };
      bar.addEventListener('mousedown', (e) => {
        const t = plots();
        if (!t) return;
        startY = e.clientY; startV = model.value;
        const r = t.getBoundingClientRect();
        box = {width: r.width, height: r.height};
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

"""Colours, CSS and figure styling shared by the interactive views and exports."""
from __future__ import annotations

import colorsys

# Component palette: colour-blind friendly, prints well, and distinct from the
# red/blue used for the two Zijderveld projections.
COMPONENT_PALETTE = [
    "#2a9d8f",  # teal
    "#e76f51",  # terracotta
    "#7b5ea7",  # violet
    "#e9a800",  # amber
    "#3a86ff",  # azure
    "#c0392b",  # crimson
    "#6b8e23",  # olive
    "#d35400",  # pumpkin
    "#16a085",  # sea green
    "#8e44ad",  # purple
]
HORIZONTAL_COLOR = "#c8102e"     # N-E projection (circles)
VERTICAL_COLOR = "#1f4e9c"       # N-Down projection (squares)
POINT_FILL = "#8c8c8c"           # publication style grey fill
POINT_EDGE = "#2b2b2b"
MEAN_COLOR = "#e76f51"
LAND_COLOR = "#e9e0cc"        # Natural Earth land on the pole globe
LAND_EDGE = "#c9bda4"
OCEAN_COLOR = "#f3f7fb"
SITE_COLOR = "#2e8b57"        # sampling sites on the globe
NET_COLOR = "#2b2b2b"

# Each application gets its own accent, so that two of these windows open side
# by side are told apart at a glance. They live together here, not in the
# applications, so that a new one cannot quietly pick a colour already in use.
# Chrome only: a data mark's colour says what the data is, never which
# application drew it.
ACCENT_DIRECTIONS = "#1f4e9c"     # navy -- PmagPy Directions
ACCENT_INTENSITY = "#6a2c5a"      # plum -- PmagPy Intensity
ACCENTS = {"pmagpy_directions": ACCENT_DIRECTIONS, "pmagpy_intensity": ACCENT_INTENSITY}
ACCENT = ACCENT_DIRECTIONS        # the default the module-level CSS below is built from

# a fixed mapping for the most common legacy names, then the palette in order
PRESET_COLORS = {"HT": "#2a9d8f", "LT": "#e9a800", "MT": "#7b5ea7", "mag": "#2a9d8f", "hem": "#e76f51",
                 "A": "#2a9d8f", "B": "#e76f51", "C": "#7b5ea7", "D": "#e9a800"}


class ComponentColors:
    """Assign a stable colour to every component *name* in a study.

    The same name (e.g. "HT") gets the same colour on every specimen, in the
    logger, on the equal-area plots of every level and in exported figures.
    """

    def __init__(self):
        self._colors: dict[str, str] = {}

    def __call__(self, name: str) -> str:
        if name not in self._colors:
            preset = PRESET_COLORS.get(name)
            used = set(self._colors.values())
            if preset and preset not in used:
                self._colors[name] = preset
            else:
                free = [c for c in COMPONENT_PALETTE if c not in used]
                self._colors[name] = free[0] if free else COMPONENT_PALETTE[len(self._colors) % len(COMPONENT_PALETTE)]
        return self._colors[name]

    def assign(self, name: str, color: str) -> None:
        self._colors[name] = color

    def as_dict(self) -> dict[str, str]:
        return dict(self._colors)


KPI_STYLE = "display:flex;gap:18px;flex-wrap:wrap;font-size:0.95rem;color:#2b2b2b;padding:4px 0"
KPI_ITEM = "white-space:nowrap"
SECTION_STYLE = ("font-weight:600;font-size:0.78rem;letter-spacing:.04em;text-transform:uppercase;"
                 "color:#5b6470;margin:4px 0 2px 0")
MUTED_STYLE = "color:#6b7280;font-size:0.85rem"
# result tables (the mean statistics): a handful of numbers should read as one
# block at the left, not stretch its columns across the whole width of the pane
STATS_TABLE_CSS = """
table { width: auto !important; border-collapse: collapse; font-size: 0.9rem; }
th, td { padding: 4px 0 4px 20px; text-align: right; white-space: nowrap; }
th:first-child, td:first-child { padding-left: 0; text-align: left; }
th { color: #5b6470; font-weight: 600; border-bottom: 1px solid #d0d4da; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
"""
# text inputs and selects side by side get one box height
INPUT_CSS = """
:host .bk-input { height: 34px; min-height: 34px; padding-top: 0; padding-bottom: 0; box-sizing: border-box; }
"""


def kpi(items) -> str:
    """HTML for a row of key figures; items are (label, value) or plain strings."""
    spans = []
    for it in items:
        if isinstance(it, tuple):
            spans.append(f'<span style="{KPI_ITEM}">{it[0]} <b>{it[1]}</b></span>')
        else:
            spans.append(f'<span style="{KPI_ITEM}">{it}</span>')
    return f'<div style="{KPI_STYLE}">' + "".join(spans) + "</div>"


def lighten(hex_color: str, amount: float = 0.75) -> str:
    """Blend a hex colour towards white (amount=1 is white)."""
    if amount <= 0:
        return hex_color
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = l + (1 - l) * amount
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


_RAW_CSS_TEMPLATE = """
:root { --pmagpy-accent: %(accent)s; --demag-accent: %(accent)s; }
.bk-root, .pn-loading { font-family: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif; }
#sidebar { padding-right: 6px; }
/* a compact header and main card: vertical space belongs to the analysis */
#header { padding: 3px 10px; height: 50px; box-sizing: border-box; }
/* the template sizes #main for its default 64px header; reclaim the difference */
#main { height: calc(100vh - 50px) !important; }
#header .title { font-size: 1.15rem; }
#header .app-header img, #header img.app-logo, .app-header img { height: 28px; width: auto; margin-right: 6px; }
.card-margin > fast-card.pn-wrapper { padding: 2px 14px !important; }
.card-margin { margin: 2px 0 !important; }
.main-margin { margin: 2px 0 0 0 !important; }
#container { height: 100vh !important; }
.demag-section { font-weight: 600; font-size: 0.8rem; letter-spacing: .04em; text-transform: uppercase;
                 color: #5b6470; margin: 6px 0 2px 0; }
.demag-kpi { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.95rem; color: #2b2b2b; padding: 4px 0; }
.demag-kpi span { white-space: nowrap; }
.demag-kpi b { color: #111; }
.demag-muted { color: #6b7280; font-size: 0.85rem; }
"""


class Theme:
    """The accent-dependent half of the styling, for one application.

    All of it comes from one colour, so giving an application its own identity
    is a line rather than a forked stylesheet. The tints are what ``lighten()``
    gives: at 0.93 and 0.86 the navy accent reproduces, to within a shade, the
    hand-picked blues these tables carried before they were derived.
    """

    def __init__(self, accent: str):
        self.accent = accent
        self.row_hover = lighten(accent, 0.93)       # a hovered table row
        self.row_selected = lighten(accent, 0.86)    # and a selected one
        self.tab_rest = lighten(accent, 0.91)        # an inactive tab
        self.tab_hover = lighten(accent, 0.84)

    def __repr__(self):
        return f"Theme({self.accent!r})"

    # the main tabs: unmistakably tabs, in the same small bold capitals as the
    # side-panel headings
    @property
    def tabs_css(self) -> str:
        return f"""
:host .bk-header {{ border-bottom: 2px solid {self.accent} !important; margin-bottom: 1px; gap: 0;
    height: 30px !important; min-height: 0 !important; }}
:host .bk-header .bk-tab {{ font-weight: 600 !important; font-size: 0.78rem !important; letter-spacing: .04em;
    text-transform: uppercase; color: #5b6470 !important; background-color: {self.tab_rest} !important;
    border: 1px solid #d0d4da !important; border-bottom: none !important; border-radius: 6px 6px 0 0 !important;
    padding: 0 16px !important; margin: 0 4px 0 0 !important;
    height: 28px !important; display: inline-flex !important; align-items: center; box-sizing: border-box; }}
:host .bk-header .bk-tab:hover {{ background-color: {self.tab_hover} !important; color: #1f2937 !important; }}
:host .bk-header .bk-tab.bk-active, :host .bk-header .bk-tab.bk-active:hover {{
    background-color: {self.accent} !important; color: #ffffff !important; border-color: {self.accent} !important; }}
:host .bk-header .bk-tab:focus, :host .bk-header .bk-tab:focus-visible {{ outline: none !important; }}
"""

    # native checkboxes with the accent colour: the browser then draws a white tick
    @property
    def checkbox_css(self) -> str:
        return f"""
:host input[type='checkbox'] {{ accent-color: {self.accent}; width: 15px; height: 15px; appearance: auto;
    -webkit-appearance: auto; background: none; border: none; }}
"""

    # Tabulator turns a row's text white when it is hovered or selected, which on
    # the pale component colours these tables carry leaves it barely readable.
    # Both states keep dark text on a tint of the accent, and a selected row is
    # picked out by weight rather than by colour.
    @property
    def table_row_css(self) -> str:
        return f"""
.tabulator-row:hover {{ background-color: {self.row_hover} !important; }}
.tabulator-row:hover .tabulator-cell, .tabulator-row:hover {{ color: #111 !important; }}
.tabulator-row.tabulator-selected, .tabulator-row.tabulator-selected:hover {{
    background-color: {self.row_selected} !important; font-weight: 700; }}
.tabulator-row.tabulator-selected, .tabulator-row.tabulator-selected .tabulator-cell,
.tabulator-row.tabulator-selected:hover .tabulator-cell {{ color: #111 !important; }}
"""

    # outline-style button groups: the active choice is a filled button, and needs
    # white text to stay readable on the accent
    @property
    def button_group_css(self) -> str:
        return f"""
.bk-btn-group .bk-btn.bk-active, .bk-btn-group .bk-btn.bk-active:hover {{ color: #ffffff !important;
    background-color: {self.accent} !important; border-color: {self.accent} !important; font-weight: 600; }}
.bk-btn-group .bk-btn {{ color: #1f2937; }}
"""

    @property
    def raw_css(self) -> str:
        return _RAW_CSS_TEMPLATE % {"accent": self.accent}


def for_app(app_id: str) -> Theme:
    """The theme for an application, by its ``app_id``; an unknown id gets the default."""
    return Theme(ACCENTS.get(app_id, ACCENT))


#: the default theme, and the module-level names built from it -- an application
#: that wants its own calls :func:`for_app` instead
DEFAULT_THEME = Theme(ACCENT)
TABS_CSS = DEFAULT_THEME.tabs_css
CHECKBOX_CSS = DEFAULT_THEME.checkbox_css
TABLE_ROW_CSS = DEFAULT_THEME.table_row_css
BUTTON_GROUP_CSS = DEFAULT_THEME.button_group_css
RAW_CSS = DEFAULT_THEME.raw_css


def style_figure(fig, hide_axes: bool = False):
    """Quiet Bokeh styling: no logo, subtle outline, thin toolbar."""
    fig.toolbar.logo = None
    fig.toolbar.autohide = True
    fig.outline_line_color = "#d0d4da"
    fig.background_fill_color = "#ffffff"
    fig.border_fill_color = "#ffffff"
    if fig.title is not None:
        fig.title.text_font_size = "11pt"
        fig.title.text_font_style = "normal"
        fig.title.text_color = "#374151"
    if hide_axes:
        fig.axis.visible = False
        fig.grid.visible = False
    else:
        fig.grid.grid_line_color = "#eef0f3"
        fig.axis.axis_line_color = "#9aa1ab"
        fig.axis.major_tick_line_color = "#9aa1ab"
        fig.axis.minor_tick_line_color = None
        fig.axis.major_label_text_color = "#374151"
        fig.axis.axis_label_text_color = "#374151"
        fig.axis.axis_label_text_font_style = "normal"
    return fig


def asset_data_uri(path: str) -> str:
    """Embed an image as a data URI (Panel templates take URLs, not files).

    Takes a full path: assets belong to an application, not to this toolkit,
    so there is no directory for it to guess at.
    """
    import base64
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")

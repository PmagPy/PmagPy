"""Theme-aware colours for PmagPy wxPython controls.

Normal and inactive controls use colours supplied by the operating system.
Semantic states use explicit foreground/background pairs so that status
colours remain readable in both light and dark appearance modes.  wxPython is
loaded only when system colours or events are needed so the semantic palette
can be tested in non-GUI environments.
"""

NORMAL = "normal"
INACTIVE = "inactive"
SUCCESS = "success"
ERROR = "error"
WARNING = "warning"
ACTION = "action"
ANALYSIS = "analysis"
UPLOAD = "upload"
NEUTRAL = "neutral"


_ROLE_ALIASES = {
    "disabled": INACTIVE,
    "empty": INACTIVE,
    "pass": SUCCESS,
    "fail": ERROR,
}

_SEMANTIC_PALETTES = {
    False: {
        SUCCESS: ("#D4EDDA", "#155724"),
        ERROR: ("#F8D7DA", "#721C24"),
        WARNING: ("#FFF3CD", "#664D03"),
        ACTION: ("#FDC68A", "#000000"),
        ANALYSIS: ("#6ECFF6", "#000000"),
        UPLOAD: ("#C4DF9B", "#000000"),
        NEUTRAL: ("#F8F8FF", "#000000"),
    },
    True: {
        SUCCESS: ("#153F2A", "#D7FBE2"),
        ERROR: ("#5C2026", "#FFE3E5"),
        WARNING: ("#4A3A0B", "#FFF0B3"),
        ACTION: ("#6B431B", "#FFE1BA"),
        ANALYSIS: ("#164B61", "#C9F1FF"),
        UPLOAD: ("#36501F", "#E0F4C0"),
        NEUTRAL: ("#3A3A44", "#F5F5FF"),
    },
}

# Base window colours and blend fraction used by ``get_tint_colours``.
_TINT_BASES = {False: "#FFFFFF", True: "#1E1E1E"}
_TINT_STRENGTH = 0.45


def _get_wx():
    """Import and return wxPython only when a GUI operation requires it."""
    import wx
    return wx


def is_dark_mode():
    """Return whether wxPython reports a dark system appearance."""
    wx = _get_wx()
    try:
        return wx.SystemSettings.GetAppearance().IsDark()
    except (AttributeError, RuntimeError):
        try:
            colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        except RuntimeError:
            return False
        return _relative_luminance(colour) < 0.5


def get_control_colours(role=NORMAL, dark=None):
    """Return a readable ``(background, foreground)`` pair for *role*.

    Parameters
    ----------
    role : str
        One of ``normal``, ``inactive``, ``success``, ``error``,
        ``warning``, ``action``, ``analysis``, ``upload``, or ``neutral``.
        The aliases ``empty``, ``disabled``, ``pass``, and ``fail`` are also
        accepted.
    dark : bool or None
        Explicit appearance used mainly for testing.  When omitted, the
        current operating-system appearance is used.
    """
    role = _ROLE_ALIASES.get(role, role)
    if role == NORMAL:
        wx = _get_wx()
        return (
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
        )
    if role == INACTIVE:
        wx = _get_wx()
        return (
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE),
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT),
        )
    if role not in _SEMANTIC_PALETTES[False]:
        raise ValueError("Unknown GUI colour role: {}".format(role))

    if dark is None:
        dark = is_dark_mode()
    background, foreground = _SEMANTIC_PALETTES[bool(dark)][role]
    return background, foreground


def style_control(control, role=NORMAL, dark=None, refresh=True):
    """Apply a theme role to a wx control and remember it for theme changes."""
    background, foreground = get_control_colours(role, dark=dark)
    control.SetBackgroundColour(background)
    control.SetForegroundColour(foreground)
    control._pmag_theme_role = _ROLE_ALIASES.get(role, role)
    if refresh:
        control.Refresh()
    return background, foreground


def get_tint_colours(colour, dark=None, strength=_TINT_STRENGTH):
    """Return a readable ``(background, foreground)`` pair tinted by *colour*.

    The background is *colour* blended into the light or dark base window
    colour, so that a row can be associated with a plotted element (e.g. the
    colour of an interpretation) without the saturated plot colour making the
    text hard to read.  The foreground is whichever of black or white
    contrasts best with that background.

    Parameters
    ----------
    colour : str
        Hexadecimal colour (``#RRGGBB``) to tint toward.
    dark : bool or None
        Explicit appearance used mainly for testing.  When omitted, the
        current operating-system appearance is used.
    strength : float
        Fraction of *colour* in the blend (0 is the base colour, 1 is
        *colour* itself).
    """
    if dark is None:
        dark = is_dark_mode()
    value = colour.lstrip("#")
    base = _TINT_BASES[bool(dark)].lstrip("#")
    blended = []
    for position in (0, 2, 4):
        colour_channel = int(value[position:position + 2], 16)
        base_channel = int(base[position:position + 2], 16)
        blended.append(int(round(
            strength * colour_channel + (1 - strength) * base_channel
        )))
    background = "#{:02X}{:02X}{:02X}".format(*blended)
    foreground = max(
        ("#000000", "#FFFFFF"),
        key=lambda candidate: contrast_ratio(background, candidate),
    )
    return background, foreground


def style_list_item(list_control, index, role=NORMAL, dark=None, refresh=True,
                    tint=None):
    """Apply a readable theme role to one row of a ``wx.ListCtrl``.

    List controls keep item colours separately from the colours of the
    control itself.  Setting only a row background can therefore combine a
    light background with the system's dark-mode foreground, making the row
    unreadable.  This helper always applies both colours and remembers the
    role so it can be reapplied after a system theme change.

    When *tint* (a ``#RRGGBB`` string) is given, the row colours come from
    ``get_tint_colours`` instead of the palette for *role*; the role is
    still remembered, along with the tint.
    """
    if tint is None:
        background, foreground = get_control_colours(role, dark=dark)
    else:
        background, foreground = get_tint_colours(tint, dark=dark)
    list_control.SetItemBackgroundColour(index, background)
    list_control.SetItemTextColour(index, foreground)
    roles = getattr(list_control, "_pmag_item_theme_roles", {})
    roles[index] = _ROLE_ALIASES.get(role, role)
    list_control._pmag_item_theme_roles = roles
    tints = getattr(list_control, "_pmag_item_theme_tints", {})
    if tint is None:
        tints.pop(index, None)
    else:
        tints[index] = tint
    list_control._pmag_item_theme_tints = tints
    if refresh:
        list_control.RefreshItem(index)
    return background, foreground


def refresh_window_colours(window):
    """Reapply remembered theme roles throughout a window hierarchy."""
    role = getattr(window, "_pmag_theme_role", None)
    if role is not None:
        style_control(window, role)
    item_roles = getattr(window, "_pmag_item_theme_roles", {})
    item_tints = getattr(window, "_pmag_item_theme_tints", {})
    for index, item_role in item_roles.items():
        if index < window.GetItemCount():
            style_list_item(
                window, index, item_role, refresh=False,
                tint=item_tints.get(index),
            )
    if item_roles:
        window.Refresh()
    for child in window.GetChildren():
        refresh_window_colours(child)


def bind_theme_updates(window):
    """Refresh custom control colours when the operating-system theme changes."""
    if getattr(window, "_pmag_theme_updates_bound", False):
        return
    wx = _get_wx()

    def on_system_colour_changed(event):
        event.Skip()
        wx.CallAfter(refresh_window_colours, window)

    window.Bind(wx.EVT_SYS_COLOUR_CHANGED, on_system_colour_changed)
    window._pmag_theme_updates_bound = True
    window._pmag_theme_update_handler = on_system_colour_changed


def _relative_luminance(colour):
    """Return WCAG relative luminance for a wx colour or hexadecimal string."""
    if isinstance(colour, str):
        value = colour.lstrip("#")
        rgb = tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))
    else:
        rgb = (colour.Red(), colour.Green(), colour.Blue())

    channels = []
    for value in rgb:
        channel = value / 255.0
        channels.append(
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
        )
    return (
        0.2126 * channels[0]
        + 0.7152 * channels[1]
        + 0.0722 * channels[2]
    )


def contrast_ratio(first, second):
    """Return the WCAG contrast ratio between two wx colours."""
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)

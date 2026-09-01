"""Helpers for exporting figures embedded in the wx GUIs."""


def save_figure(figure, path, dpi=300):
    """Save *figure* without changing its live GUI canvas or dimensions."""
    original_canvas = figure.canvas
    original_size = tuple(figure.get_size_inches())
    original_dpi = figure.dpi

    try:
        figure.savefig(path, dpi=dpi)
    finally:
        # The figure is still displayed by its original wx canvas.  Keep that
        # relationship and its on-screen dimensions intact after exporting.
        figure.set_canvas(original_canvas)
        figure.set_dpi(original_dpi)
        figure.set_size_inches(original_size, forward=False)

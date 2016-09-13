
search_help = """Filters the list of interpretations below such that all remaining entries will contain the string searched for in one of their columns."""

eqarea_help = """Eqarea plot of the high level interpretations at the currently selected level.
plot interactions:
  - click and drag to
    zoom or pan
    (default=zoom)
  - right click to toggle
    zoom or pan
  - middle click to home
  - double click to view
    selected fit
fit symbols and colors:
  - diamond = selected
    fit
  - small diamond =
    bad fit
  - circle = good fit
  - black = fisher mean
    of displayed data
check sample orient symbols:
  - triangle = wrong
    drill direction
  - delta = wrong
    compass direction
  - dotted plane = rotated
    sample direction
    during measurement
    (lighter points are
    lower hemisphere)"""

logger_help = """List of all interpretations currently displayed on the high level mean plot to the right. The interpretations displayed both on the plot and list can be changed using the level box and the level name box which display the level at which interpretations are being displayed (ie. site, sample, study, location) and the name of the corrisponding site, sample, study, or location they are being displayed for.
colored entries:
  - blue: current fit
  - red: bad fit
  - dark blue: highlighted
    (grey on mac)
interaction:
  - right click to toggle
    fit bad
  - double click to select"""

level_box_help = """Current level at which interpretations are displayed on high level mean plot bellow and listed on the right. (choose study for all interpretations)"""

level_names_help = """The name of the current site, sample, study, or location for which interpretations are displayed"""

mean_type_help = """The type of mean to calculate and display on the high level mean plot using all currently displayed interpretations"""

mean_fit_help = """Which interpretations to display on the high level mean plot"""

show_help = """The unit of the interpretations displayed bellow, where specimen means the vectors/planes on the plot are specimen components and samples or sites means they are fisher means of those components. (further fisher means of the displayed interpretations are only allowed at the specimen level)"""

coordinates_box_help = """The current coordinate system and other coordinate options. (note: if there is not enough data to rotate any specimen's measurement data to a given coordinate system it will not be an option in the dropdown menu. If you think this is wrong and there is a coordinate system missing check to insure that azimuth and bed orentation are available in your sample data imported into the GUI)"""

tmin_box_help = """The chosen lower bound. (note: does not change current interpretation's lower bound or display current interpretation's lower bound that can be found in list to left)"""

tmax_box_help = """The chosen upper bound. (note: does not change current interpretation's upper bound or display current interpretation's upper bound that can be found in list to left)"""

color_box_help = """The chosen color to apply to newly generated fits or highlighted fits as according to button pressed bellow"""

name_box_help = """Name to give to newly generated fits or highlighted fits as according to button pressed bellow"""

add_all_help = """Adds a new interpretation to all specimens with the available upper and lower bounds selected in the tmin and tmax box above. The new interpretations will all have the name, color, and bounds selected above. (note: if nothing is entered above a default name and color will be given and the uppermost and lowermost bound taken for the new interpretation in all specimens)"""

add_fit_btn_help = """Adds a new interpretation to all highlighted specimens. Where highlighted specimens means any specimen for which you have highlighted at least one already existing interpretation. Highlighting more than one interpretation will not add multipule fits to the same specimen. (note: if nothing is entered above a default name and color will be given and the uppermost and lowermost bound taken for the new interpretation in all specimens)"""

delete_fit_btn_help = """Delete all highlighted interpretations."""

apply_changes_help = """Applies the above name, color, and bounds information to all highlighted specimens in the list. (note: that if the bounds selected don't exist in the measurement data of any of the specimens selected they will be skipped)"""

switch_stats_btn_help = """Cycles through all currently plotted top level fisher means, will be blank if there are none and will do nothing if there is one."""

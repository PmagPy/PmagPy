
zij_help = """Zijderveld plot of current specimen measurement data and fits
plot interactions:
  - click and drag to
    zoom or pan
    (default=zoom)
  - right click to toggle
    zoom or pan
  - middle click to home
  - double click 2 measurements
    to set them as bounds

fit symbols:
  - diamond = selected
    fit
  - small diamond =
    bad fit
  - circle = good fit"""

spec_eqarea_help = """Specimen Eqarea plot shows measurement data in white and all fits
plot interactions:
  - click and drag to
    zoom or pan
    (default=zoom)
  - right click to toggle
    zoom or pan
  - middle click to home
  - double click to view
    selected fit

fit symbols:
  - diamond = selected
    fit
  - small diamond =
    bad fit
  - circle = good fit"""

MM0_help = """M/M0 plot for data with the bounds of fits
plot interactions:
  - click and drag to
    zoom or pan
    (default=zoom)
  - right click to toggle
    zoom or pan
  - middle click to home

fit symbols:
  - diamond = selected
    fit
  - small diamond =
    bad fit
  - circle = good fit"""

high_level_eqarea_help = """High Level Mean Eqarea plot
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

logger_help = """ List of all measurement entries for current specimen
column labels:
  - i: index
  - Step: type of step
    N = NRM
    T = Thermal
    AF = Alternating
    Field
  - Dec: Declination
  - Inc: Inclination
  - M: Magnetic Moment
colored entries:
  - blue: measurements
    that are part of
    current fit
  - red: bad measurement
  - dark blue: highlighted
    (grey on mac)
interaction:
  - right click to toggle
    measurement bad
  - double click two 
    measurements to set
    new bounds of current
    fit"""

specimens_box_help = """Displays current specimen and has dropdown of all specimens for which there is valid measurement data. You can also enter another specimen name into the box and when you hit enter the GUI will try to switch to that specimen if it exists."""

nextbutton_help = """Switches current specimen to next specimen. Hotkey: ctrl-left"""

prevbutton_help = """Switches current specimen to previous specimen. Hotkey: ctrl-right"""

coordinates_box_help = """Shows current coordinate system and has a dropdown menu of all coordinate systems for which there are specimens with valid measurement data.
Hotkeys:
  - specimen: ctrl-P
  - geographic: ctrl-g
  - tilt-corrected: ctrl-t"""

orthogonal_box_help = """Zijderveld orientation options"""

fit_box_help = """Displays current fit name and has dropdown of all fits for the current specimen. Fits can be renamed here by typing new name into the box and hitting enter.
Hotkeys:
  - ctrl-up: previous fit
  - ctrl-down: next fit"""

add_fit_button_help = """Adds a new fit to the current specimen. Hotkey: ctrl-n"""

tmin_box_help = """Shows lower bound of current fit and has dropdown menu of all measurement steps."""

tmax_box_help = """Shows upper bound of current fit and has dropdown menu of all measurement steps."""

save_fit_btn_help = """Saves current interpretations to demag_gui.redo file so they can be reloaded in another session. Hotkey: ctrl-s"""

delete_fit_btn_help = """Deletes current fit and reverts your current fit to the previous fit. Hotkey: ctrl-D"""

PCA_type_help = """Shows the current fit's regression or mean type."""

plane_display_help = """How to display plane fits on eqarea plots:
bfv = Best Fit Vector
wp = Whole plane"""

level_box_help = """Shows the current level at which interpretations will be displayed on the high level mean eqarea plot in the far right of the GUI."""

level_names_help  = """Shows the available samples, sites, locations, or studies which can be displayed on the high level mean eqarea plot"""

mean_type_help = """Type of mean to preform on all interpretations currently plotted on the high level mean eqarea plot"""

mean_fit_help = """Which interpretations to display in the high level mean plot. If 'All' then all interpretations are displayed reguardless of name, else only interpretations of name == value will be displayed"""

warning_help = """Message box to display any relevent problems with the current specimen and it's interpretations to the user."""

switch_stats_btn_help = """These buttons allow you to cycle through all current high level mean statistics in the case where you are doing a fisher by polarity mean."""





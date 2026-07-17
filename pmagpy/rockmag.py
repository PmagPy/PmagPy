import pandas as pd
import numpy as np
import copy
import json
import ast

from scipy.optimize import minimize, brent, least_squares, minimize_scalar, brentq
from scipy.signal import savgol_filter, find_peaks
from scipy.special import erf, owens_t
from scipy.interpolate import UnivariateSpline

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patches as patches

from pmagpy.pmag import _resolve_rng
from pmagpy.version import version as pmagpy_version

try:
    import ipywidgets as widgets
    from ipywidgets import HBox, VBox, Output, Dropdown, RadioButtons, Checkbox,  IntSlider, FloatSlider, IntRangeSlider
    from IPython.display import HTML, display

except ImportError:
    widgets = None
    display = None

try:
    from bokeh.plotting import figure, show
    from bokeh.layouts import gridplot
    from bokeh.models import HoverTool, ColumnDataSource, PointDrawTool, CustomJS, Div
    from bokeh.embed import components
    from bokeh.palettes import Category10
    from bokeh.models.widgets import DataTable, TableColumn
    from bokeh.layouts import column
    _HAS_BOKEH = True
except ImportError:
    _HAS_BOKEH = False
try:
    from lmfit import Parameters, Model  # for fitting
    from lmfit.models import SkewedGaussianModel
except ImportError:
    Parameters = None
    Model = None
    SkewedGaussianModel = None

try:
    import statsmodels.api as sm
    lowess = sm.nonparametric.lowess
except ImportError:
    sm = None
    lowess = None


def _check_ipywidgets():
    if widgets is None:
        raise ImportError(
            "ipywidgets is required for interactive functions. "
            "Install it with: pip install ipywidgets"
        )


def _check_bokeh():
    if not _HAS_BOKEH:
        raise ImportError(
            "bokeh is required for interactive plotting. "
            "Install it with: pip install bokeh"
        )


def _check_lmfit():
    if Parameters is None:
        raise ImportError(
            "lmfit is required for curve fitting/unmixing. "
            "Install it with: pip install lmfit"
        )


def _check_statsmodels():
    if lowess is None:
        raise ImportError(
            "statsmodels is required for LOWESS smoothing. "
            "Install it with: pip install statsmodels"
        )
    
mpl_to_bokeh_markers = {
    ".": "dot",
    ",": "dot",
    "o": "circle",
    "v": "inverted_triangle",
    "^": "triangle",
    "<": "triangle",
    ">": "triangle",
    "1": "triangle",
    "2": "inverted_triangle",
    "3": "triangle",
    "4": "inverted_triangle",
    "s": "square",
    "p": "square",
    "*": "asterisk",
    "h": "hex",
    "H": "hex",
    "+": "plus",
    "x": "x",
    "X": "x",
    "D": "diamond",
    "d": "diamond",
    "|": "dash",
    "_": "dash",
}

# general I/O functions
# ------------------------------------------------------------------------------------------------------------------

def dict_in_native_python(d):
    """Convert NumPy scalar values in a dict to native Python scalars.

    Parameters
    ----------
    d : dict
        Dictionary whose values may include NumPy scalar types
        (e.g. np.float64, np.int64, np.bool_).

    Returns
    -------
    dict
        A new dictionary with the same keys as `d` but with any
        NumPy scalar values replaced by their native Python
        equivalents (float, int, bool). Non‐NumPy values are
        left unchanged.
    """
    return {k: v.item() if isinstance(v, np.generic) else v for k, v in d.items()}


def map_legend_location(matplotlib_loc):
    """
    Maps a Matplotlib legend location to a Bokeh legend location.
    Falls back to 'top_left' if no direct mapping exists.

    Parameters
    ----------
    matplotlib_loc : str
        Matplotlib legend location (e.g., 'upper right', 'lower left').

    Returns
    -------
    str
        Corresponding Bokeh legend location.
    """
    mapping = {
        'best': 'top_left',
        'upper right': 'top_right',
        'upper left': 'top_left',
        'lower left': 'bottom_left',
        'lower right': 'bottom_right',
        'right': 'right',
        'center left': 'left',
        'center right': 'right',
        'lower center': 'bottom_center',
        'upper center': 'top_center',
        'center': 'center',
    }
    return mapping.get(matplotlib_loc, 'top_left')


def interactive_specimen_selection(measurements):
    """
    Creates and displays a dropdown widget for selecting a specimen from a given
    DataFrame of measurements.

    Parameters
    ----------
    measurements : pd.DataFrame
        The DataFrame containing measurement data with a column 'specimen'. It is
        expected to have at least this column where 'specimen' identifies the
        specimen name.

    Returns
    -------
    ipywidgets.Dropdown
        A dropdown widget allowing for the selection of a specimen. The initial
        selection in the dropdown is set to the first specimen option.
    """
    _check_ipywidgets()
    # Extract unique specimen names from the measurements DataFrame
    specimen_options = measurements['specimen'].unique().tolist()

    # Set the initial selection to the first specimen option, if available
    selected_specimen_name = specimen_options[0] if specimen_options else None

    # Create a dropdown for specimen selection
    specimen_dropdown = widgets.Dropdown(
        options=specimen_options,
        description='Specimen:',
        value=selected_specimen_name
    )

    # Display the dropdown widget
    display(specimen_dropdown)

    return specimen_dropdown


def interactive_specimen_experiment_selection(measurements):
    """
    Creates interactive dropdown widgets for selecting a specimen and its associated
    experiment from a measurements DataFrame.

    Parameters
    ----------
    measurements : pd.DataFrame
        DataFrame containing measurement data with at least two columns: 'specimen' and
        'experiment'. The 'specimen' column holds the specimen names while the 'experiment'
        column holds the experiment identifiers associated with each specimen.

    Returns
    -------
    tuple of ipywidgets.Dropdown
        A tuple containing two dropdown widgets. The first widget allows for selecting a
        specimen, and the second widget allows for selecting an experiment associated with
        the chosen specimen. The experiment dropdown is dynamically updated based on the
        specimen selection.
    """
    _check_ipywidgets()
    specimen_dropdown = widgets.Dropdown(
        options = measurements['specimen'].unique(),
        description = 'specimen:',
        disabled = False,
    )

    experiment_dropdown = widgets.Dropdown(
        options = measurements['experiment'].unique(),
        description = 'Experiment:',
        disabled = False,
    )
    # make sure to set the default value of the experiment dropdown to the first experiment in the specimen dropdown
    experiment_dropdown.options = measurements[measurements['specimen']==specimen_dropdown.value]['experiment'].unique()

    # make sure to update the experiment dropdown based on the specimen selected
    def update_experiment(*args):
        experiment_dropdown.options = measurements[measurements['specimen']==specimen_dropdown.value]['experiment'].unique()

    specimen_dropdown.observe(update_experiment, 'value')

    # display the dropdowns
    display(specimen_dropdown, experiment_dropdown)
    
    return specimen_dropdown, experiment_dropdown


def make_experiment_df(measurements, exclude_method_codes=None):
    """
    Creates a DataFrame of unique experiments from the measurements DataFrame.

    Parameters
    ----------
    measurements : pd.DataFrame
        The DataFrame containing measurement data with columns 'specimen', 
        'method_codes', and 'experiment'.
    exclude_method_codes : list of str, optional
        List of method codes to exclude from the output DataFrame. Rows with 
        'method_codes' containing any of these substrings will be removed.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing unique combinations of 'specimen', 'method_codes', 
        and 'experiment'.
    """
    if exclude_method_codes is not None:
        mask = ~measurements["method_codes"].apply(
            lambda x: any(code in x for code in exclude_method_codes)
        )
        measurements = measurements.loc[mask]

    experiments = (
        measurements.groupby(["specimen", "method_codes", "experiment"])
        .size()
        .reset_index()
        .iloc[:, :3]
    )
    return experiments


def experiment_selection(measurements, experiment_name):
    """
    This function filters a measurements DataFrame to return only the rows 
    that correspond to the specified experiment name. 
    
    Parameters
    ----------
    measurements : pd.DataFrame
        The DataFrame containing measurement data with an 'experiment' column.
    experiment_name : str
        The name of the experiment to select from the DataFrame.
    Returns
    -------
    pd.DataFrame
        A DataFrame containing only the rows corresponding to the specified experiment.
    """
    if 'experiment' not in measurements.columns:
        raise ValueError("The measurements DataFrame must contain an 'experiment' column.")
    if not isinstance(experiment_name, str):
        raise TypeError("The experiment_name must be a string.")
    if experiment_name not in measurements['experiment'].unique():
        raise ValueError(f"Experiment '{experiment_name}' not found in the measurements DataFrame.")
    # Filter the DataFrame for the specified experiment
    selected_experiment = measurements[measurements['experiment'] == experiment_name].reset_index(drop=True)
    selected_experiment = clean_out_na(selected_experiment)
    return selected_experiment


def clean_out_na(dataframe):
    """
    Cleans a DataFrame by removing columns and rows that contain only NaN values.
    
    Args:
        dataframe (pd.DataFrame): The DataFrame to be cleaned.
    Returns:
        pd.DataFrame: A cleaned DataFrame with all-NaN columns and rows removed.   
    """
    cleaned_df = dataframe.dropna(axis=1, how='all')
    return cleaned_df


def convert_temperature(temp_array, input_unit, output_unit):
    """
    Convert temperatures between Kelvin and Celsius.

    Parameters
    ----------
    temp_array : array-like
        Temperatures in `input_unit`.
    input_unit : {'K', 'C'}
        Unit of the input temperatures.
    output_unit : {'K', 'C'}
        Desired unit for output temperatures.

    Returns
    -------
    numpy.ndarray
        Temperatures converted to `output_unit`.

    Raises
    ------
    ValueError
        If `input_unit` or `output_unit` is not 'K' or 'C'.
    """
    temps = np.asarray(temp_array, dtype=float)
    if input_unit == output_unit:
        return temps
    if input_unit == "K" and output_unit == "C":
        return temps - 273.15
    if input_unit == "C" and output_unit == "K":
        return temps + 273.15
    raise ValueError(f"Unsupported unit conversion: {input_unit} -> {output_unit}")


def plot_ms_t(
    data,
    temperature_column="meas_temp",
    magnetization_column="magn_mass",
    input_unit="K",
    plot_unit="K",
    interactive=False,
    return_figure=False,
    show_plot=True,
    size=(6, 3),
    legend_location="upper left",
):
    """
    Plot magnetization versus temperature in static or interactive mode.

    Parameters
    ----------
    data : pandas.DataFrame or array-like
        Table or array containing temperature and magnetization data.
    temperature_column : str, default 'meas_temp'
        Name of the temperature column in `data`.
    magnetization_column : str, default 'magn_mass'
        Name of the magnetization column in `data`.
    input_unit : {'K', 'C'}, default 'K'
        Unit of the input temperature data.
    plot_unit : {'K', 'C'}, default 'K'
        Unit for the x-axis display.
    interactive : bool, default False
        If True, use Bokeh for an interactive plot.
    return_figure : bool, default False
        If True, return the figure object(s). Assign to capture, e.g.:
            fig, ax = plot_ms_t(..., return_figure=True)
    show_plot : bool, default True
        If True, display the plot immediately.
    size : tuple(float, float), default (6, 3)
        Figure size in inches (Matplotlib) or height for Bokeh.
    legend_location : str, default 'upper left'
        Legend location in Matplotlib terms.

    Returns
    -------
    tuple or layout or None
        - If `return_figure=True` and `interactive=False`, returns (fig, ax).
        - If `return_figure=True` and `interactive=True`, returns the Bokeh
          layout object.
        - Otherwise, returns None.
    """
    # raw data arrays
    T_raw = np.asarray(data[temperature_column], dtype=float)
    M = np.asarray(data[magnetization_column], dtype=float)

    # convert to desired plotting unit
    T = convert_temperature(T_raw, input_unit, plot_unit)
    x_label = "Temperature (°C)" if plot_unit == "C" else "Temperature (K)"

    # plotting
    if interactive:
        _check_bokeh()
        bokeh_loc = map_legend_location(legend_location)
        tools = [
            HoverTool(tooltips=[("T", "@x"), ("M", "@y")]),
            "pan,box_zoom,wheel_zoom,reset,save",
        ]
        height = int(size[1] * 96)
        p = figure(
            title="M vs T",
            x_axis_label=x_label,
            y_axis_label="Magnetization",
            tools=tools,
            sizing_mode="stretch_width",
            height=height,
        )
        p.line(T, M, legend_label="M(T)", line_width=2)
        p.scatter(T, M, size=6, alpha=0.6, legend_label="M(T)")
        p.legend.location = bokeh_loc
        p.legend.click_policy = "hide"
        layout = gridplot([[p]], sizing_mode="stretch_width")
        if show_plot:
            show(layout)
        if return_figure:
            return layout
        return None

    fig, ax = plt.subplots(figsize=size)
    ax.plot(T, M, "o-", label="M(T)")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Magnetization")
    ax.set_title("M vs T")
    ax.legend(loc=legend_location)
    ax.grid(True)
    if show_plot:
        plt.show()
    if return_figure:
        return fig, ax
    return None


# MPMS functions
# ------------------------------------------------------------------------------------------------------------------

def extract_mpms_data_dc(df, specimen_name):
    """
    Extracts and separates MPMS data for a specified specimen from a DataFrame.

    This function filters data for the given specimen and separates it based on
    MagIC measurement method codes. It specifically extracts data corresponding to
    'LP-FC' (Field Cooled), 'LP-ZFC' (Zero Field Cooled), 'LP-CW-SIRM:LP-MC' (Room
    Temperature SIRM measured upon cooling), and 'LP-CW-SIRM:LP-MW' (Room Temperature
    SIRM measured upon Warming). For each method code, if the data is not available,
    an empty DataFrame with the same columns as the specimen data is returned.

    Parameters:
        df (pd.DataFrame): DataFrame containing MPMS measurement data.
        specimen_name (str): Name of the specimen to filter data for.

    Returns:
        tuple: A tuple containing four DataFrames:
            - fc_data: Data filtered for 'LP-FC' method if available, otherwise an empty
              DataFrame.
            - zfc_data: Data filtered for 'LP-ZFC' method if available, otherwise an empty
              DataFrame.
            - rtsirm_cool_data: Data filtered for 'LP-CW-SIRM:LP-MC' method if available,
              otherwise an empty DataFrame.
            - rtsirm_warm_data: Data filtered for 'LP-CW-SIRM:LP-MW' method if available,
              otherwise an empty DataFrame.
    """
    specimen_df = df[df["specimen"] == specimen_name]
    empty_df = pd.DataFrame(columns=specimen_df.columns)

    # If the 'method_codes' column is missing, return empty DataFrames.
    if "method_codes" not in specimen_df.columns:
        return empty_df, empty_df, empty_df, empty_df

    # Filter for each method code if available, otherwise use empty DataFrame.
    fc_data = (
        specimen_df[specimen_df["method_codes"].str.contains("LP-FC", na=False)]
        if specimen_df["method_codes"].str.contains("LP-FC", na=False).any()
        else empty_df
    )
    zfc_data = (
        specimen_df[specimen_df["method_codes"].str.contains("LP-ZFC", na=False)]
        if specimen_df["method_codes"].str.contains("LP-ZFC", na=False).any()
        else empty_df
    )
    rtsirm_cool_data = (
        specimen_df[
            specimen_df["method_codes"].str.contains("LP-CW-SIRM:LP-MC", na=False)
        ]
        if specimen_df["method_codes"].str.contains("LP-CW-SIRM:LP-MC", na=False).any()
        else empty_df
    )
    rtsirm_warm_data = (
        specimen_df[
            specimen_df["method_codes"].str.contains("LP-CW-SIRM:LP-MW", na=False)
        ]
        if specimen_df["method_codes"].str.contains("LP-CW-SIRM:LP-MW", na=False).any()
        else empty_df
    )

    return fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data


def plot_mpms_dc(
    fc_data=None,
    zfc_data=None,
    rtsirm_cool_data=None,
    rtsirm_warm_data=None,
    fc_color="#1f77b4",
    zfc_color="#ff7f0e",
    rtsirm_cool_color="#17becf",
    rtsirm_warm_color="#d62728",
    fc_marker="d",
    zfc_marker="p",
    rtsirm_cool_marker="s",
    rtsirm_warm_marker="o",
    symbol_size=4,
    interactive=False,
    plot_derivative=False,
    return_figure=False,
    show_plot=True,
    drop_first=False,
    drop_last=False,
):
    """
    Plots MPMS DC data and optional derivatives, omitting empty panels.

    Parameters:
        fc_data (DataFrame or None): Field-cooled data.
        zfc_data (DataFrame or None): Zero-field-cooled data.
        rtsirm_cool_data (DataFrame or None): RTSIRM cooling data.
        rtsirm_warm_data (DataFrame or None): RTSIRM warming data.
        fc_color, zfc_color, rtsirm_cool_color, rtsirm_warm_color (str):
            HEX color codes.
        fc_marker, zfc_marker, rtsirm_cool_marker, rtsirm_warm_marker (str):
            Matplotlib-style markers.
        symbol_size (int): Marker size.
        interactive (bool): If True, use Bokeh.
        plot_derivative (bool): If True, plot dM/dT curves.
        return_figure (bool): If True, return the figure/grid.
        show_plot (bool): If True, display the plot.
        drop_first (bool): If True, drop first row of each series.
        drop_last (bool): If True, drop last row of each series.

    Returns:
        Bokeh grid or Matplotlib fig/axes tuple, or None.
    """
    def trim(df):
        if df is None or df.empty:
            return None
        df = df.reset_index(drop=True)
        if drop_first:
            df = df.iloc[1:].reset_index(drop=True)
        if drop_last:
            df = df.iloc[:-1].reset_index(drop=True)
        return df

    fc = trim(fc_data)
    zfc = trim(zfc_data)
    rc = trim(rtsirm_cool_data)
    rw = trim(rtsirm_warm_data)

    if plot_derivative:
        def deriv(df):
            return None if df is None else thermomag_derivative(
                df["meas_temp"], df["magn_mass"]
            )
        fcd = deriv(fc)
        zfcd = deriv(zfc)
        rcd = deriv(rc)
        rwd = deriv(rw)

    fc_zfc_present = (fc is not None) or (zfc is not None)  
    rtsirm_present = (rc is not None) or (rw is not None)  

    if interactive:
        _check_bokeh()
        tools = [HoverTool(tooltips=[("T","@x"),("M","@y")]), "pan,box_zoom,wheel_zoom,reset,save"]
        figs = []  

        if fc_zfc_present:  
            p0 = figure(title="LTSIRM Data", x_axis_label="Temperature (K)", 
                        y_axis_label="Magnetization (Am2/kg)", tools=tools, 
                        sizing_mode="stretch_width",height=400)  
            if fc is not None:  
                p0.line(fc["meas_temp"], fc["magn_mass"], color=fc_color, legend_label="FC")  
                p0.scatter(fc["meas_temp"], fc["magn_mass"], marker=mpl_to_bokeh_markers.get(fc_marker), 
                           size=symbol_size, color=fc_color, legend_label="FC")  
            if zfc is not None:  
                p0.line(zfc["meas_temp"], zfc["magn_mass"], color=zfc_color, legend_label="ZFC")  
                p0.scatter(zfc["meas_temp"], zfc["magn_mass"], marker=mpl_to_bokeh_markers.get(zfc_marker), 
                           size=symbol_size, color=zfc_color, legend_label="ZFC")  
            p0.legend.click_policy="hide"  
            p0.xaxis.axis_label_text_font_style = "normal"
            p0.yaxis.axis_label_text_font_style = "normal"
            figs.append(p0)  

        if rtsirm_present:  
            p1 = figure(title="RTSIRM Data", x_axis_label="Temperature (K)", 
                        y_axis_label="Magnetization (Am2/kg)", tools=tools, 
                        sizing_mode="stretch_width",height=400)  
            if rc is not None:  
                p1.line(rc["meas_temp"], rc["magn_mass"], color=rtsirm_cool_color, legend_label="cool")  
                p1.scatter(rc["meas_temp"], rc["magn_mass"], marker=mpl_to_bokeh_markers.get(rtsirm_cool_marker), 
                           size=symbol_size, color=rtsirm_cool_color, legend_label="cool")  
            if rw is not None:  
                p1.line(rw["meas_temp"], rw["magn_mass"], color=rtsirm_warm_color, legend_label="warm")  
                p1.scatter(rw["meas_temp"], rw["magn_mass"], marker=mpl_to_bokeh_markers.get(rtsirm_warm_marker), 
                           size=symbol_size, color=rtsirm_warm_color, legend_label="warm")  
            p1.legend.click_policy="hide"  
            p1.xaxis.axis_label_text_font_style = "normal"
            p1.yaxis.axis_label_text_font_style = "normal"
            figs.append(p1)  

        # separate derivative panels  
        if plot_derivative and fc_zfc_present:  
            p2 = figure(title="LTSIRM Derivative", x_axis_label="Temperature (K)", 
                        y_axis_label="dM/dT", tools=tools, 
                        sizing_mode="stretch_width",height=400)  
            if fcd is not None: 
                p2.line(fcd["T"], fcd["dM_dT"], color=fc_color, legend_label="FC dM/dT")
                p2.scatter(fcd["T"], fcd["dM_dT"], marker=mpl_to_bokeh_markers.get(fc_marker), 
                           size=symbol_size, color=fc_color, legend_label="FC dM/dT")  
            if zfcd is not None: 
                p2.line(zfcd["T"], zfcd["dM_dT"], color=zfc_color, legend_label="ZFC dM/dT")  
                p2.scatter(zfcd["T"], zfcd["dM_dT"], marker=mpl_to_bokeh_markers.get(zfc_marker), 
                           size=symbol_size, color=zfc_color, legend_label="ZFC dM/dT")
            p2.legend.click_policy="hide" 
            p2.xaxis.axis_label_text_font_style = "normal"
            p2.yaxis.axis_label_text_font_style = "normal"        
            figs.append(p2)  

        if plot_derivative and rtsirm_present:  
            p3 = figure(title="RTSIRM Derivative", x_axis_label="Temperature (K)", 
                        y_axis_label="dM/dT", tools=tools, 
                        sizing_mode="stretch_width",height=400)  
            if rcd is not None: 
                p3.line(rcd["T"], rcd["dM_dT"], color=rtsirm_cool_color, legend_label="cool dM/dT")  
                p3.scatter(rcd["T"], rcd["dM_dT"], marker=mpl_to_bokeh_markers.get(rtsirm_cool_marker), 
                           size=symbol_size, color=rtsirm_cool_color, legend_label="cool dM/dT")
            if rwd is not None: 
                p3.line(rwd["T"], rwd["dM_dT"], color=rtsirm_warm_color, legend_label="warm dM/dT")  
                p3.scatter(rwd["T"], rwd["dM_dT"], marker=mpl_to_bokeh_markers.get(rtsirm_warm_marker), 
                           size=symbol_size, color=rtsirm_warm_color, legend_label="warm dM/dT")
            p3.legend.click_policy="hide"  
            p3.xaxis.axis_label_text_font_style = "normal"
            p3.yaxis.axis_label_text_font_style = "normal"
            figs.append(p3)  

        layout = gridplot([figs[:2], figs[2:]], sizing_mode="stretch_width")  
        if show_plot:
            show(layout)
        return layout if return_figure else None  

    # Matplotlib branch  
    rows = 1 + (1 if plot_derivative else 0)  
    cols = 2  
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))  
    axes = axes.reshape(rows, cols)  

    if not fc_zfc_present:  
        axes[0,0].set_visible(False)  
        if plot_derivative:
            axes[1,0].set_visible(False)
    if not rtsirm_present:  
        axes[0,1].set_visible(False)  
        if plot_derivative:
            axes[1,1].set_visible(False)

    if fc_zfc_present:  
        ax = axes[0,0]  
        if fc is not None: 
            ax.plot(fc["meas_temp"], fc["magn_mass"], color=fc_color, marker=fc_marker, label="FC")  
        if zfc is not None:
            ax.plot(zfc["meas_temp"], zfc["magn_mass"], color=zfc_color, marker=zfc_marker, label="ZFC")  
        ax.set_title("LTSIRM Data")
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Magnetization")
        ax.legend()
        ax.grid(True)

    if rtsirm_present:  
        ax = axes[0,1]  
        if rc is not None: 
            ax.plot(rc["meas_temp"], rc["magn_mass"], color=rtsirm_cool_color, marker=rtsirm_cool_marker, label="cool")
        if rw is not None: 
            ax.plot(rw["meas_temp"], rw["magn_mass"], color=rtsirm_warm_color, marker=rtsirm_warm_marker, label="warm")
        ax.set_title("RTSIRM Data")
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Magnetization")
        ax.legend()
        ax.grid(True)  

    if plot_derivative and fc_zfc_present:
        ax = axes[1,0]
        if fcd is not None:
            ax.plot(fcd["T"], fcd["dM_dT"], color=fc_color, marker=fc_marker, label="FC dM/dT")
        if zfcd is not None:
            ax.plot(zfcd["T"], zfcd["dM_dT"], color=zfc_color, marker=zfc_marker, label="ZFC dM/dT")
        ax.set_title("LTSIRM Derivative")
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("dM/dT")
        ax.legend()
        ax.grid(True)  

    if plot_derivative and rtsirm_present:  
        ax = axes[1,1]  
        if rcd is not None:
            ax.plot(rcd["T"], rcd["dM_dT"], color=rtsirm_cool_color, marker=rtsirm_cool_marker, label="cool dM/dT")
        if rwd is not None:
            ax.plot(rwd["T"], rwd["dM_dT"], color=rtsirm_warm_color, marker=rtsirm_warm_marker, label="warm dM/dT")
        ax.set_title("RTSIRM Derivative")
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("dM/dT")
        ax.legend()
        ax.grid(True)

    fig.tight_layout()  
    if show_plot:
        plt.show()
    return fig if return_figure else None  


def make_mpms_plots_dc(measurements):
    """Create a UI to select specimen and plot MPMS data in Matplotlib or Bokeh.

    Parameters:
        measurements (pandas.DataFrame): DataFrame with 'specimen' and
            'method_codes'.
    """
    _check_ipywidgets()
    experiments = (
        measurements.groupby(["specimen", "method_codes"])
        .size()
        .reset_index()
        .iloc[:, :2]
    )
    filtered = experiments[
        experiments["method_codes"].isin(
            ["LP-FC", "LP-ZFC", "LP-CW-SIRM:LP-MC", "LP-CW-SIRM:LP-MW"]
        )
    ]
    specimen_options = filtered["specimen"].unique().tolist()

    specimen_dd = widgets.Dropdown(
        options=specimen_options, description="Specimen:"
    )
    library_rb = widgets.RadioButtons(
        options=["Bokeh", "Matplotlib"], description="Plot with:"
    )
    out = widgets.Output()

    def _update(change=None):
        spec = specimen_dd.value
        fc_data, zfc_data, rts_c, rts_w = extract_mpms_data_dc(
            measurements, spec
        )

        with out:
            out.clear_output(wait=True)
            if library_rb.value == "Matplotlib":
                plot_mpms_dc(
                    fc_data,
                    zfc_data,
                    rts_c,
                    rts_w,
                    interactive=False,
                    plot_derivative=True,
                    show_plot=True,
                )
            else:
                grid = plot_mpms_dc(
                    fc_data,
                    zfc_data,
                    rts_c,
                    rts_w,
                    interactive=True,
                    plot_derivative=True,
                    return_figure=True,
                    show_plot=False,
                )
                script, div = components(grid)
                display(HTML(div + script))

    specimen_dd.observe(_update, names="value")
    library_rb.observe(_update, names="value")

    ui = widgets.VBox([widgets.HBox([specimen_dd, library_rb]), out])
    display(ui)
    _update()
    
    
def calc_verwey_estimate(temps, mags, 
                    t_range_background_min=50,
                    t_range_background_max=250,
                    excluded_t_min=75,
                    excluded_t_max=150,
                    poly_deg=3):
    """
    Estimate the Verwey transition temperature and remanence loss of magnetite from MPMS data.
    Plots the magnetization data, background fit, and resulting magnetite curve, and 
    optionally the zero-crossing.

    Parameters
    ----------
    temps : pd.Series
        Series representing the temperatures at which magnetization measurements were taken.
    mags : pd.Series
        Series representing the magnetization measurements.
    t_range_background_min : int or float, optional
        Minimum temperature for the background fitting range. Default is 50.
    t_range_background_max : int or float, optional
        Maximum temperature for the background fitting range. Default is 250.
    excluded_t_min : int or float, optional
        Minimum temperature to exclude from the background fitting range. Default is 75.
    excluded_t_max : int or float, optional
        Maximum temperature to exclude from the background fitting range. Default is 150.
    poly_deg : int, optional
        Degree of the polynomial for background fitting. Default is 3.
    """
    
    temps.reset_index(drop=True, inplace=True)
    mags.reset_index(drop=True, inplace=True)

    dM_dT_df = thermomag_derivative(temps, mags)
    temps_dM_dT = dM_dT_df['T']

    temps_dM_dT_filtered_indices = [i for i in np.arange(len(temps_dM_dT)) if ((float(temps_dM_dT[i]) > float(t_range_background_min)) and (float(temps_dM_dT[i])  < float(excluded_t_min)) ) or ((float(temps_dM_dT[i]) > float(excluded_t_max)) and (float(temps_dM_dT[i])  < float(t_range_background_max)))]
    temps_dM_dT_filtered = dM_dT_df['T'][temps_dM_dT_filtered_indices]
    dM_dT_filtered = dM_dT_df['dM_dT'][temps_dM_dT_filtered_indices]

    poly_background_fit = np.polyfit(temps_dM_dT_filtered, dM_dT_filtered, poly_deg)
    dM_dT_filtered_polyfit = np.poly1d(poly_background_fit)(temps_dM_dT_filtered)

    residuals = dM_dT_filtered - dM_dT_filtered_polyfit
    ss_tot = np.sum((dM_dT_filtered - np.mean(dM_dT_filtered)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    temps_dM_dT_background_indices = [i for i in np.arange(len(temps_dM_dT)) if ((float(temps_dM_dT[i]) > float(t_range_background_min)) and (float(temps_dM_dT[i])  < float(t_range_background_max)))]
    temps_dM_dT_background = dM_dT_df['T'][temps_dM_dT_background_indices]
    temps_dM_dT_background.reset_index(drop=True, inplace=True)
    dM_dT_background = dM_dT_df['dM_dT'][temps_dM_dT_background_indices]
    dM_dT_polyfit = np.poly1d(poly_background_fit)(temps_dM_dT_background)

    mgt_dM_dT = dM_dT_polyfit - dM_dT_background 
    mgt_dM_dT.reset_index(drop = True, inplace=True)

    temps_background_indices = [i for i in np.arange(len(temps)) if ((float(temps[i]) > float(t_range_background_min)) and (float(temps[i])  < float(t_range_background_max)))]
    temps_background = temps[temps_background_indices]

    poly_func = np.poly1d(poly_background_fit)
    background_curve = np.cumsum(poly_func(temps_background) * np.gradient(temps_background))

    last_background_temp = temps_background.iloc[-1]    
    last_background_mag = background_curve[-1]
    target_temp_index = np.argmin(np.abs(temps - last_background_temp))
    mags_value = mags[target_temp_index]
    background_curve_adjusted = background_curve + (mags_value - last_background_mag)

    mags_background = mags[temps_background_indices]
    mgt_curve = mags_background - background_curve_adjusted
    
    verwey_estimate = calc_zero_crossing(temps_dM_dT_background, mgt_dM_dT)[-1]
    
    remanence_loss = np.trapezoid(mgt_dM_dT, temps_dM_dT_background)

    return dM_dT_df, verwey_estimate, remanence_loss, r_squared, temps_background, temps_dM_dT_background, mgt_dM_dT, dM_dT_polyfit, background_curve_adjusted, mgt_curve


def verwey_estimate(temps, mags, 
                    t_range_background_min=50,
                    t_range_background_max=250,
                    excluded_t_min=75,
                    excluded_t_max=150,
                    poly_deg=3,
                    plot_zero_crossing=False,
                    plot_title=None,
                    measurement_marker='o', measurement_color='FireBrick',
                    background_fit_marker='s', background_fit_color='Teal',
                    magnetite_marker='d', magnetite_color='RoyalBlue',
                    verwey_marker='*', verwey_color='Pink',
                    verwey_size=10,
                    markersize=3.5):
    """
    Estimate the Verwey transition temperature and remanence loss of magnetite from MPMS data.
    Plots the magnetization data, background fit, and resulting magnetite curve, and 
    optionally the zero-crossing.

    Parameters
    ----------
    temps : pd.Series
        Series representing the temperatures at which magnetization measurements were taken.
    mags : pd.Series
        Series representing the magnetization measurements.
    t_range_background_min : int or float, optional
        Minimum temperature for the background fitting range. Default is 50.
    t_range_background_max : int or float, optional
        Maximum temperature for the background fitting range. Default is 250.
    excluded_t_min : int or float, optional
        Minimum temperature to exclude from the background fitting range. Default is 75.
    excluded_t_max : int or float, optional
        Maximum temperature to exclude from the background fitting range. Default is 150.
    poly_deg : int, optional
        Degree of the polynomial for background fitting. Default is 3.
    plot_zero_crossing : bool, optional
        If True, plots the zero-crossing of the second derivative. Default is False.
    plot_title : str, optional
        Title for the plot. Default is None.
    measurement_marker : str, optional
        Marker symbol for measurement data. Default is 'o'.
    measurement_color : str, optional
        Color for measurement data. Default is 'black'.
    background_fit_marker : str, optional
        Marker symbol for background fit data. Default is 's'.
    background_fit_color : str, optional
        Color for background fit data. Default is 'C1'.
    magnetite_marker : str, optional
        Marker symbol for magnetite data. Default is 'd'.
    magnetite_color : str, optional
        Color for magnetite data. Default is 'C0'.
    verwey_marker : str, optional
        Marker symbol used to denote the Verwey transition estimate on the plot. Default is '*'.
    verwey_color : str, optional
        Color of the marker representing the Verwey transition estimate. Default is 'Pink'.
    verwey_size : int, optional
        Size of the marker used for the Verwey transition estimate. Default is 10.
    markersize : float, optional
        Size of the markers. Default is 3.5.

    Returns
    -------
    verwey_estimate : float
        Estimated Verwey transition temperature.
    remanence_loss : float
        Estimated remanence loss.

    Examples
    --------
    >>> temps = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    >>> mags = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    >>> verwey_estimate(temps, mags)
    (75.0, 0.5)
    """
    dM_dT_df, verwey_estimate, remanence_loss, r_squared, temps_background, temps_dM_dT_background, mgt_dM_dT, dM_dT_polyfit, background_curve_adjusted, mgt_curve = calc_verwey_estimate(temps, mags,
                    t_range_background_min=t_range_background_min,
                    t_range_background_max=t_range_background_max,
                    excluded_t_min=excluded_t_min,
                    excluded_t_max=excluded_t_max,
                    poly_deg=poly_deg)
        
    fig = plt.figure(figsize=(12,5))
    fig.canvas.header_visible = False
    ax0 = fig.add_subplot(1,2,1)
    ax0.plot(temps, mags, marker=measurement_marker, markersize=markersize, color=measurement_color, 
             label='measurement')
    ax0.plot(temps_background, background_curve_adjusted, marker=background_fit_marker, markersize=markersize, color=background_fit_color, 
             label='background fit')
    ax0.plot(temps_background, mgt_curve, marker=magnetite_marker, markersize=markersize, color=magnetite_color, 
             label='magnetite (meas. minus background)')
    verwey_y_value = np.interp(verwey_estimate, temps_background, mgt_curve)
    ax0.plot(verwey_estimate, verwey_y_value, verwey_marker, color=verwey_color, markersize=verwey_size,
         markeredgecolor='black', markeredgewidth=1,
         label='Verwey estimate' + ' (' + str(round(verwey_estimate,1)) + ' K)')
    ax0.set_ylabel('M (Am$^2$/kg)')
    ax0.set_xlabel('T (K)')
    ax0.legend(loc='upper right')
    ax0.grid(True)
    ax0.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
    if plot_title is not None:
        ax0.set_title(plot_title)

    ax1 = fig.add_subplot(1,2,2)
    ax1.plot(dM_dT_df['T'], dM_dT_df['dM_dT'], marker=measurement_marker, markersize=markersize, color=measurement_color, 
             label='measurement')
    ax1.plot(temps_dM_dT_background, dM_dT_polyfit, marker=background_fit_marker, markersize=markersize, color=background_fit_color, 
             label='background fit'+ ' (r$^2$ = ' + str(round(r_squared,3)) + ')' )
    ax1.plot(temps_dM_dT_background, mgt_dM_dT, marker=magnetite_marker, markersize=markersize, color=magnetite_color, 
             label='magnetite (background fit minus measurement)')
    verwey_y_value = np.interp(verwey_estimate, temps_dM_dT_background, mgt_dM_dT)
    ax1.plot(verwey_estimate, verwey_y_value, verwey_marker, color=verwey_color, markersize=verwey_size,
         markeredgecolor='black', markeredgewidth=1,
         label='Verwey estimate' + ' (' + str(round(verwey_estimate,1)) + ' K)')
    rectangle = patches.Rectangle((excluded_t_min, ax1.get_ylim()[0]), excluded_t_max - excluded_t_min, 
                                  ax1.get_ylim()[1] - ax1.get_ylim()[0], 
                                  linewidth=0, edgecolor=None, facecolor='gray', 
                                  alpha=0.3)
    ax1.add_patch(rectangle)
    rect_legend_patch = patches.Patch(color='gray', alpha=0.3, label='excluded from background fit')
    handles, labels = ax1.get_legend_handles_labels()
    handles.append(rect_legend_patch)  # Add the rectangle legend patch
    ax1.legend(handles=handles, loc='lower right')
    ax1.set_ylabel('dM/dT (Am$^2$/kg/K)')
    ax1.set_xlabel('T (K)')
    ax1.grid(True)
    ax1.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
    if plot_title is not None:
        ax1.set_title(plot_title)
    
    if plot_zero_crossing:
        ax2 = zero_crossing(temps_dM_dT_background, mgt_dM_dT, make_plot=True)

    return verwey_estimate, remanence_loss


def interactive_verwey_estimate(measurements, specimen_dropdown, method_dropdown, figsize=(11, 5)):
    """
    Create an interactive widget for estimating the Verwey transition temperature from low temperature remanence measurements.

    This function displays interactive sliders and controls for adjusting background fitting parameters
    and temperature ranges, allowing the user to visually estimate the Verwey transition temperature (T_v)
    for a selected specimen and measurement method. The function updates plots in real-time according to user input,
    enabling exploration of parameter effects on the calculated transition.

    Parameters
    ----------
    measurements : pandas.DataFrame
        low temperature remanence measurement data containing temperature and magnetization columns for multiple specimens.
    specimen_dropdown : ipywidgets.Dropdown
        Dropdown widget for selecting the specimen to analyze.
    method_dropdown : ipywidgets.Dropdown
        Dropdown widget for selecting the measurement method ('LP-FC' or 'LP-ZFC').
    figsize : tuple of (float, float), optional
        Size of the matplotlib figure, by default (11, 5).

    Notes
    -----
    - The function uses `ipywidgets` for interactive controls and `matplotlib` for visualization.
    - The background fit and excluded temperature ranges can be adjusted using sliders.
    - The polynomial degree of the background fit is also adjustable.
    - A reset button restores the default slider values.
    - The function relies on supporting functions such as `extract_mpms_data_dc`, `thermomag_derivative`, and `calc_verwey_estimate`.

    Returns
    -------
    None
        This function is intended for use in Jupyter notebooks or environments that support interactive widgets and inline plotting.
        It displays interactive sliders and plots but does not return a value.

    Examples
    --------
    >>> interactive_verwey_estimate(measurements_df, specimen_dropdown, method_dropdown)
    Displays an interactive interface for estimating the Verwey transition temperature.
    """
    _check_ipywidgets()
    selected_specimen_name = specimen_dropdown.value
    selected_method = method_dropdown.value

    fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data = extract_mpms_data_dc(measurements, selected_specimen_name)
    if selected_method == 'LP-FC':
        temps = fc_data['meas_temp']
        mags = fc_data['magn_mass']
    elif selected_method == 'LP-ZFC':
        temps = zfc_data['meas_temp']
        mags = zfc_data['magn_mass']
    temps.reset_index(drop=True, inplace=True)
    mags.reset_index(drop=True, inplace=True)
    dM_dT_df = thermomag_derivative(temps, mags)
    temps_dM_dT = dM_dT_df['T']

    # Determine a fixed width for the descriptions to align the sliders
    description_width = '250px'  # Adjust this based on the longest description
    slider_total_width = '600px'  # Total width of the slider widget including the description

    description_style = {'description_width': description_width}
    slider_layout = widgets.Layout(width=slider_total_width)  # Set the total width of the slider widget

    # Update sliders to use IntRangeSlider
    background_temp_range_slider = IntRangeSlider(
        value=[60, 250], min=0, max=300, step=1,
        description='Background Temperature Range (K):',
        layout=slider_layout, style=description_style
    )

    excluded_temp_range_slider = IntRangeSlider(
        value=[75, 150], min=0, max=300, step=1,
        description='Excluded Temperature Range (K):',
        layout=slider_layout, style=description_style
    )

    poly_deg_slider = IntSlider(
        value=3, min=1, max=5, step=1,
        description='Background Fit Polynomial Degree:',
        layout=slider_layout, style=description_style
    )

    # Function to reset sliders to initial values
    def reset_sliders(b):
        background_temp_range_slider.value = (60, 250)
        excluded_temp_range_slider.value = (75, 150)
        poly_deg_slider.value = 3

    # Create reset button
    reset_button = widgets.Button(description="Reset to Default Values", layout=widgets.Layout(width='200px'))
    reset_button.on_click(reset_sliders)
    
    # title_label = widgets.Label(value='Adjust Parameters for ' + selected_specimen_name + ' ' + selected_method + ' fit')

    # Add the reset button to the UI
    ui = widgets.VBox([ 
        # title_label,
        background_temp_range_slider, 
        excluded_temp_range_slider, 
        poly_deg_slider,
        reset_button
    ])

    display(ui)

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=figsize)
    fig.canvas.header_visible = False

    def update_plot(*args):
        ax0, ax1 = ax
        ax0.clear()
        ax1.clear()
        # get values from sliders
        t_range_background_min = background_temp_range_slider.value[0]
        t_range_background_max = background_temp_range_slider.value[1]
        excluded_t_min = excluded_temp_range_slider.value[0]
        excluded_t_max = excluded_temp_range_slider.value[1]
        poly_deg = poly_deg_slider.value

        # recalculate verwey estimate
        dM_dT_df, verwey_estimate, remanence_loss, r_squared, temps_background, temps_dM_dT_background, mgt_dM_dT, dM_dT_polyfit, background_curve_adjusted, mgt_curve = calc_verwey_estimate(temps, mags,
                    t_range_background_min=t_range_background_min,
                    t_range_background_max=t_range_background_max,
                    excluded_t_min=excluded_t_min,
                    excluded_t_max=excluded_t_max,
                    poly_deg=poly_deg)
    
        ax0.plot(temps, mags, marker='o', markersize=3.5, color='FireBrick', 
                label='measurement')
        ax0.plot(temps_background, background_curve_adjusted, marker='s', markersize=3.5, color='Teal', 
                label='background fit')
        ax0.plot(temps_background, mgt_curve, marker='d', markersize=3.5, color='RoyalBlue', 
                label='magnetite (meas. minus background)')
        verwey_y_value = np.interp(verwey_estimate, temps_background, mgt_curve)
        ax0.plot(verwey_estimate, verwey_y_value, '*', color='Pink', markersize=10,
            markeredgecolor='black', markeredgewidth=1,
            label='Verwey estimate' + ' (' + str(round(verwey_estimate,1)) + ' K)')
        ax0.set_ylabel('M (Am$^2$/kg)')
        ax0.set_xlabel('T (K)')
        ax0.legend(loc='upper right')
        ax0.grid(True)
        ax0.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
        
        ax1.plot(dM_dT_df['T'], dM_dT_df['dM_dT'], marker='o', markersize=3.5, color='FireBrick', 
                label='measurement')
        ax1.plot(temps_dM_dT_background, dM_dT_polyfit, marker='s', markersize=3.5, color='Teal', 
                label='background fit'+ ' (r$^2$ = ' + str(round(r_squared,3)) + ')' )
        ax1.plot(temps_dM_dT_background, mgt_dM_dT, marker='d', markersize=3.5, color='RoyalBlue', 
                label='magnetite (background fit minus measurement)')
        verwey_y_value = np.interp(verwey_estimate, temps_dM_dT_background, mgt_dM_dT)
        ax1.plot(verwey_estimate, verwey_y_value, '*', color='Pink', markersize=10,
            markeredgecolor='black', markeredgewidth=1,
            label='Verwey estimate' + ' (' + str(round(verwey_estimate,1)) + ' K)')
        rectangle = patches.Rectangle((excluded_t_min, ax1.get_ylim()[0]), excluded_t_max - excluded_t_min, 
                                    ax1.get_ylim()[1] - ax1.get_ylim()[0], 
                                    linewidth=0, edgecolor=None, facecolor='gray', 
                                    alpha=0.3)
        ax1.add_patch(rectangle)
        rect_legend_patch = patches.Patch(color='gray', alpha=0.3, label='excluded from background fit')
        handles, labels = ax1.get_legend_handles_labels()
        handles.append(rect_legend_patch)  # Add the rectangle legend patch
        ax1.legend(handles=handles, loc='lower right')
        ax1.set_ylabel('dM/dT (Am$^2$/kg/K)')
        ax1.set_xlabel('T (K)')
        ax1.grid(True)
        ax1.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))


    # Attach observers
    background_temp_range_slider.observe(update_plot, names='value')
    excluded_temp_range_slider.observe(update_plot, names='value')
    poly_deg_slider.observe(update_plot, names='value')
    reset_button.on_click(update_plot)

    update_plot()


def interactive_verwey_specimen_method_selection(measurements):
    """
    Creates and displays dropdown widgets for selecting a specimen and the corresponding
    available method codes (specifically 'LP-FC' and 'LP-ZFC') from a given DataFrame of measurements.
    This function filters the measurements to include only those with desired method codes,
    dynamically updates the method dropdown based on the selected specimen, and organizes
    the dropdowns vertically in the UI.

    Parameters:
        measurements (pd.DataFrame): The DataFrame containing measurement data with columns
                                     'specimen' and 'method_codes'. It is expected to have
                                     at least these two columns where 'specimen' identifies
                                     the specimen name and 'method_codes' contains the method
                                     codes associated with each measurement.

    Returns:
        tuple: A tuple containing the specimen dropdown widget (`ipywidgets.Dropdown`)
               and the method dropdown widget (`ipywidgets.Dropdown`). The specimen dropdown
               allows for the selection of a specimen, and the method dropdown updates to
               display only the methods available for the selected specimen. The initial
               selection in the specimen dropdown is set to the first specimen option.

    Note:
        The method dropdown is initially populated based on the methods available for the
        first selected specimen. The available methods are specifically filtered for 'LP-FC'
        and 'LP-ZFC' codes.
    """
    _check_ipywidgets()
    # Filter to get specimens with desired method codes
    experiments = measurements.groupby(['specimen', 'method_codes']).size().reset_index().iloc[:, :2]
    filtered_experiments = experiments[experiments['method_codes'].isin(['LP-FC', 'LP-ZFC'])]
    specimen_options = filtered_experiments['specimen'].unique().tolist()

    selected_specimen_name = specimen_options[0]  # Example initial selection

    # Dropdown for specimen selection
    specimen_dropdown = widgets.Dropdown(
        options=specimen_options,
        description='Specimen:',
        value=selected_specimen_name
    )

    # Method dropdown initialized with placeholder options
    method_dropdown = widgets.Dropdown(
        description='Method:',
    )

    # Function to update method options based on selected specimen
    def update_method_options(change):
        selected_specimen = change['new']
        # Filter experiments to get methods available for the selected specimen
        available_methods = filtered_experiments[filtered_experiments['specimen'] == selected_specimen]['method_codes'].tolist()
        # Update method dropdown options and reset its value
        method_dropdown.options = available_methods
        if available_methods:
            method_dropdown.value = available_methods[0]
        else:
            method_dropdown.value = None

    # Register the update function with specimen dropdown
    specimen_dropdown.observe(update_method_options, names='value')

    # Initially populate method dropdown based on the first selected specimen
    update_method_options({'new': selected_specimen_name})

    # Creating a UI layout using VBox to organize the dropdowns vertically
    ui_layout = widgets.VBox([specimen_dropdown, method_dropdown])

    # Display the UI layout
    display(ui_layout)
    
    return specimen_dropdown, method_dropdown


def verwey_estimate_multiple_specimens(specimens_with_params, measurements):
    """
    Analyze Verwey transitions for a list of specimens with unique parameters.
    
    This function uses either field-cooled (FC) or zero-field cooled (ZFC) data depending on the 
    method_codes provided in each specimen's parameters. If "LP-FC" is found in the colon-delimited 
    method_codes, FC data is used; if "LP-ZFC" is found, ZFC data is used.
    
    Parameters
    ----------
    specimens_with_params : list of dict
        List of specimen dictionaries. Each dictionary should contain:
            - 'specimen_name' : str
              The name of the specimen.
            - 'params' : dict
              Dictionary containing:
                - 't_range_background_min' : int or float
                - 't_range_background_max' : int or float
                - 'excluded_t_min' : int or float
                - 'excluded_t_max' : int or float
                - 'poly_deg' : int
                - 'method_codes' : str
                  Colon-delimited string that must include either "LP-FC" or "LP-ZFC".
    
    measurements : object
        Measurements dataframe in MagIC format.
    
    Returns
    -------
    pd.DataFrame
        DataFrame containing the Verwey transition estimates and the input parameters for each specimen.
        Columns include:
            - 'specimen'
            - 'critical_temp'
            - 'critical_temp_type'
            - 'remanence_loss'
        plus the additional parameters from the input.
    
    Raises
    ------
    ValueError
        If neither "LP-FC" nor "LP-ZFC" is found in the method_codes for a specimen.
    Exception
        Propagates exceptions raised during data extraction or analysis.
    """
    verwey_estimates_and_params = []

    # Process each specimen with its unique parameters
    for specimen in specimens_with_params:
        specimen_name = specimen['specimen_name']
        params = specimen['params']
        
        # Extract method codes and determine whether to use FC or ZFC data
        method_codes = params.get('method_codes', '')
        codes = method_codes.split(':')
        
        # Extract the measurement data for the specimen
        fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data = extract_mpms_data_dc(measurements, specimen_name)
        
        if "LP-FC" in codes:
            data = fc_data
        elif "LP-ZFC" in codes:
            data = zfc_data
        else:
            raise ValueError(f"Specimen {specimen_name} does not have a valid method code ('LP-FC' or 'LP-ZFC').")
        
        temps = data['meas_temp']
        mags = data['magn_mass']
        
        # Estimate Verwey transition using selected data
        vt_estimate, rem_loss = verwey_estimate(
            temps,
            mags,
            t_range_background_min=params['t_range_background_min'],
            t_range_background_max=params['t_range_background_max'],
            excluded_t_min=params['excluded_t_min'],
            excluded_t_max=params['excluded_t_max'],
            poly_deg=params['poly_deg'],
            plot_title=specimen_name
        )
        
        record = {
            'specimen': specimen_name,
            'critical_temp': vt_estimate,
            'critical_temp_type': 'Verwey',
            'remanence_loss': rem_loss
        }
        record.update(params)
        verwey_estimates_and_params.append(record)
    
    return pd.DataFrame(verwey_estimates_and_params)


def thermomag_derivative(temps, mags, drop_first=False, drop_last=False):
    """
    Calculates the derivative of magnetization with respect to temperature and optionally
    drops the data corresponding to the highest and/or lowest temperature.

    Parameters:
        temps (pd.Series): A pandas Series representing the temperatures at which
                           magnetization measurements were taken.
        mags (pd.Series): A pandas Series representing the magnetization measurements.
        drop_last (bool): Optional; whether to drop the last row from the resulting
                          DataFrame. Defaults to False. Useful when there is an
                          artifact associated with the end of the experiment.
        drop_first (bool): Optional; whether to drop the first row from the resulting
                           DataFrame. Defaults to False. Useful when there is an
                          artifact associated with the start of the experiment.

    Returns:
        pd.DataFrame: A pandas DataFrame with two columns:
                      'T' - Midpoint temperatures for each temperature interval.
                      'dM_dT' - The derivative of magnetization with respect to temperature.
                      If drop_last is True, the last temperature point is excluded.
                      If drop_first is True, the first temperature point is excluded.
    """
    temps = temps.reset_index(drop=True)
    mags = mags.reset_index(drop=True)
    
    dT = temps.diff()
    dM = mags.diff()
    dM_dT = dM / dT
    dM_dT_real = dM_dT[1:]
    dM_dT_real.reset_index(drop=True, inplace=True)

    temps_dM_dT = [temps[n] + dT[n + 1] / 2 for n in range(len(temps) - 1)]
    temps_dM_dT = pd.Series(temps_dM_dT)

    dM_dT_df = pd.DataFrame({'T': temps_dM_dT, 'dM_dT': dM_dT_real})

    # Drop the last row if specified
    if drop_last:
        dM_dT_df = dM_dT_df[:-1].reset_index(drop=True)
    
    # Drop the first row if specified
    if drop_first:
        dM_dT_df = dM_dT_df[1:].reset_index(drop=True)
    
    return dM_dT_df


def calc_zero_crossing(dM_dT_temps, dM_dT):
    """
    Calculate the temperature at which the second derivative of magnetization with respect to 
    temperature crosses zero. This value provides an estimate of the peak of the derivative 
    curve that is more precise than the maximum value.

    The function computes the second derivative of magnetization (dM/dT) with respect to 
    temperature, identifies the nearest points around the maximum value of the derivative, 
    and then calculates the temperature at which this second derivative crosses zero using 
    linear interpolation.

    Parameters:
        dM_dT_temps (pd.Series): A pandas Series representing temperatures corresponding to
                                 the first derivation of magnetization with respect to temperature.
        dM_dT (pd.Series): A pandas Series representing the first derivative of 
                           magnetization with respect to temperature.
    Returns:
        float: The estimated temperature at which the second derivative of magnetization 
               with respect to temperature crosses zero.

    Note:
        The function assumes that the input series `dM_dT_temps` and `dM_dT` are related to 
        each other and are of equal length.
    """    
    max_dM_dT_temp = dM_dT_temps[dM_dT.idxmax()]
    
    d2M_dT2 = thermomag_derivative(dM_dT_temps, dM_dT)
    d2M_dT2_T_array = d2M_dT2['T'].to_numpy()
    max_index = np.searchsorted(d2M_dT2_T_array, max_dM_dT_temp)

    d2M_dT2_T_before = d2M_dT2['T'][max_index-1]
    d2M_dT2_before = d2M_dT2['dM_dT'][max_index-1]
    d2M_dT2_T_after = d2M_dT2['T'][max_index]
    d2M_dT2_after = d2M_dT2['dM_dT'][max_index]

    zero_cross_temp = d2M_dT2_T_before + ((d2M_dT2_T_after - d2M_dT2_T_before) / (d2M_dT2_after - d2M_dT2_before)) * (0 - d2M_dT2_before)

    return d2M_dT2, d2M_dT2_T_before, d2M_dT2_before, d2M_dT2_T_after, d2M_dT2_after, zero_cross_temp

def zero_crossing(dM_dT_temps, dM_dT, make_plot=False, xlim=None,
                  verwey_marker='*', verwey_color='Pink',
                  verwey_size=10,):
    """
    Calculate the temperature at which the second derivative of magnetization with respect to 
    temperature crosses zero. This value provides an estimate of the peak of the derivative 
    curve that is more precise than the maximum value.

    The function computes the second derivative of magnetization (dM/dT) with respect to 
    temperature, identifies the nearest points around the maximum value of the derivative, 
    and then calculates the temperature at which this second derivative crosses zero using 
    linear interpolation.

    Parameters:
        dM_dT_temps (pd.Series): A pandas Series representing temperatures corresponding to
                                 the first derivation of magnetization with respect to temperature.
        dM_dT (pd.Series): A pandas Series representing the first derivative of 
                           magnetization with respect to temperature.
        make_plot (bool, optional): If True, a plot will be generated. Defaults to False.
        xlim (tuple, optional): A tuple specifying the x-axis limits for the plot. Defaults to None.
        verwey_marker : str, optional
            Marker symbol used to denote the Verwey transition estimate on the plot. Default is '*'.
        verwey_color : str, optional
            Color of the marker representing the Verwey transition estimate. Default is 'Pink'.
        verwey_size : int, optional
            Size of the marker used for the Verwey transition estimate. Default is 10.

    Returns:
        float: The estimated temperature at which the second derivative of magnetization 
               with respect to temperature crosses zero.

    Note:
        The function assumes that the input series `dM_dT_temps` and `dM_dT` are related to 
        each other and are of equal length.
    """    
    
    d2M_dT2, d2M_dT2_T_before, d2M_dT2_before, d2M_dT2_T_after, d2M_dT2_after, zero_cross_temp = calc_zero_crossing(dM_dT_temps, dM_dT)
    
    if make_plot:
        fig = plt.figure(figsize=(12,4))
        ax0 = fig.add_subplot(1,1,1)
        ax0.plot(d2M_dT2['T'], d2M_dT2['dM_dT'], '.-', color='purple', label='magnetite (background fit minus measurement)')
        ax0.plot(d2M_dT2_T_before, d2M_dT2_before, marker='o', markerfacecolor='none', markeredgecolor='red')
        ax0.plot(d2M_dT2_T_after, d2M_dT2_after, marker='o', markerfacecolor='none', markeredgecolor='red')
        ax0.plot(zero_cross_temp, 0, verwey_marker, color=verwey_color, markersize=verwey_size, markeredgecolor='black')
        label = f'{zero_cross_temp:.1f} K'
        ax0.text(zero_cross_temp+2, 0, label, color='black', 
                verticalalignment='center', horizontalalignment='left',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        ax0.set_ylabel('d$^2$M/dT$^2$')
        ax0.set_xlabel('T (K)')
        ax0.grid(True)
        ax0.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
        if xlim is not None:
            ax0.set_xlim(xlim)
        plt.show()
        
    return zero_cross_temp


def goethite_removal(rtsirm_warm_data, 
                     rtsirm_cool_data,
                     t_min=150, t_max=290, poly_deg=2,
                     rtsirm_cool_color='#17becf', rtsirm_warm_color='#d62728',
                     symbol_size=4, return_data=False):
    """
    Analyzes and visualizes the removal of goethite signal from Room Temperature Saturation
    Isothermal Remanent Magnetization (RTSIRM) warming and cooling data. The function fits
    a polynomial to the RTSRIM warming curve between specified temperature bounds to model
    the goethite contribution, then subtracts this fit from the original data. The corrected
    and uncorrected magnetizations are plotted, along with their derivatives, to assess the
    effect of goethite removal.

    Parameters:
        rtsirm_warm_data (pd.DataFrame): DataFrame containing 'meas_temp' and 'magn_mass' columns
                                         for RTSIRM warming data.
        rtsirm_cool_data (pd.DataFrame): DataFrame containing 'meas_temp' and 'magn_mass' columns
                                         for RTSIRM cooling data.
        t_min (int, optional): Minimum temperature for polynomial fitting. Default is 150.
        t_max (int, optional): Maximum temperature for polynomial fitting. Default is 290.
        poly_deg (int, optional): Degree of the polynomial to fit. Default is 2.
        rtsirm_cool_color (str, optional): Color code for plotting cooling data. Default is '#17becf'.
        rtsirm_warm_color (str, optional): Color code for plotting warming data. Default is '#d62728'.
        symbol_size (int, optional): Size of the markers in the plots. Default is 4.
        return_data (bool, optional): If True, returns the corrected magnetization data for both
                                      warming and cooling. Default is False.

    Returns:
        Tuple[pd.Series, pd.Series]: Only if return_data is True. Returns two pandas Series
                                     containing the corrected magnetization data for the warming
                                     and cooling sequences, respectively.
    """
    
    rtsirm_warm_temps = rtsirm_warm_data['meas_temp']
    rtsirm_warm_mags = rtsirm_warm_data['magn_mass']
    rtsirm_cool_temps = rtsirm_cool_data['meas_temp']
    rtsirm_cool_mags = rtsirm_cool_data['magn_mass']
    
    rtsirm_warm_temps.reset_index(drop=True, inplace=True)
    rtsirm_warm_mags.reset_index(drop=True, inplace=True)
    rtsirm_cool_temps.reset_index(drop=True, inplace=True)
    rtsirm_cool_mags.reset_index(drop=True, inplace=True)
    
    rtsirm_warm_temps_filtered_indices = [i for i in np.arange(len(rtsirm_warm_temps)) if ((float(rtsirm_warm_temps[i]) > float(t_min)) and (float(rtsirm_warm_temps[i])  < float(t_max)) )]
    rtsirm_warm_temps_filtered = rtsirm_warm_temps[rtsirm_warm_temps_filtered_indices]
    rtsirm_warm_mags_filtered = rtsirm_warm_mags[rtsirm_warm_temps_filtered_indices]
    
    geothite_fit = np.polyfit(rtsirm_warm_temps_filtered, rtsirm_warm_mags_filtered, poly_deg)
    rtsirm_warm_mags_polyfit = np.poly1d(geothite_fit)(rtsirm_warm_temps)
    rtsirm_cool_mags_polyfit = np.poly1d(geothite_fit)(rtsirm_cool_temps)
    
    rtsirm_warm_mags_corrected = rtsirm_warm_mags - rtsirm_warm_mags_polyfit
    rtsirm_cool_mags_corrected = rtsirm_cool_mags - rtsirm_cool_mags_polyfit
    
    fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))
    
    axs[0, 0].plot(rtsirm_warm_temps, rtsirm_warm_mags, color=rtsirm_warm_color, 
                   marker='o', linestyle='-', markersize=symbol_size, label='RTSIRM Warming')
    axs[0, 0].plot(rtsirm_cool_temps, rtsirm_cool_mags, color=rtsirm_cool_color, 
                   marker='o', linestyle='-', markersize=symbol_size, label='RTSIRM Cooling')
    axs[0, 0].plot(rtsirm_warm_temps, rtsirm_warm_mags_polyfit, color=rtsirm_warm_color, 
                   linestyle='--', label='goethite fit')
    axs[0, 1].plot(rtsirm_warm_temps, rtsirm_warm_mags_corrected, color=rtsirm_warm_color, 
                   marker='s', linestyle='-', markersize=symbol_size, label='RTSIRM Warming (goethite removed)')
    axs[0, 1].plot(rtsirm_cool_temps, rtsirm_cool_mags_corrected, color=rtsirm_cool_color, 
                   marker='s', linestyle='-', markersize=symbol_size, label='RTSIRM Cooling (goethite removed)')
    
    ax0 = axs[0, 0] 
    rectangle = patches.Rectangle((t_min, ax0.get_ylim()[0]), t_max - t_min, 
                            ax0.get_ylim()[1] - ax0.get_ylim()[0], 
                            linewidth=0, edgecolor=None, facecolor='gray', 
                            alpha=0.3)
    ax0.add_patch(rectangle)
    rect_legend_patch = patches.Patch(color='gray', alpha=0.3, label='excluded from background fit')
    handles, labels = ax0.get_legend_handles_labels()
    handles.append(rect_legend_patch)  # Add the rectangle legend patch
    
    for ax in axs[0, :]:
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Magnetization (Am$^2$/kg)")
        ax.legend()
        ax.grid(True)
        ax.set_xlim(0, 300)
             
    rtsirm_cool_derivative = thermomag_derivative(rtsirm_cool_data['meas_temp'], 
                                                       rtsirm_cool_data['magn_mass'], drop_first=True)
    rtsirm_warm_derivative = thermomag_derivative(rtsirm_warm_data['meas_temp'], 
                                                       rtsirm_warm_data['magn_mass'], drop_last=True)
    
    rtsirm_cool_derivative_corrected = thermomag_derivative(rtsirm_cool_data['meas_temp'], 
                                                       rtsirm_cool_mags_corrected, drop_first=True)
    rtsirm_warm_derivative_corrected = thermomag_derivative(rtsirm_warm_data['meas_temp'], 
                                                       rtsirm_warm_mags_corrected, drop_last=True)

    axs[1, 0].plot(rtsirm_cool_derivative['T'], rtsirm_cool_derivative['dM_dT'], 
                   marker='o', linestyle='-', color=rtsirm_cool_color, markersize=symbol_size, label='RTSIRM Cooling Derivative')
    axs[1, 0].plot(rtsirm_warm_derivative['T'], rtsirm_warm_derivative['dM_dT'], 
                   marker='o', linestyle='-', color=rtsirm_warm_color, markersize=symbol_size, label='RTSIRM Warming Derivative')        
    axs[1, 1].plot(rtsirm_cool_derivative_corrected['T'], rtsirm_cool_derivative_corrected['dM_dT'], 
                   marker='s', linestyle='-', color=rtsirm_cool_color, markersize=symbol_size, label='RTSIRM Cooling Derivative\n(goethite removed)')
    axs[1, 1].plot(rtsirm_warm_derivative_corrected['T'], rtsirm_warm_derivative_corrected['dM_dT'], 
                   marker='s', linestyle='-', color=rtsirm_warm_color, markersize=symbol_size, label='RTSIRM Warming Derivative\n(goethite removed)')  
    for ax in axs[1, :]:
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("dM/dT")
        ax.legend()
        ax.grid(True)
        ax.set_xlim(0, 300)

    fig.tight_layout()
    plt.show()

    if return_data:
        rtsirm_warm_adjusted = pd.DataFrame({'meas_temp': rtsirm_warm_temps, 'corrected_magn_mass': rtsirm_warm_mags_corrected})
        rtsirm_cool_adjusted = pd.DataFrame({'meas_temp': rtsirm_cool_temps, 'corrected_magn_mass': rtsirm_cool_mags_corrected})
        return rtsirm_warm_adjusted, rtsirm_cool_adjusted
    
    
def goethite_removal_interactive(measurements, specimen_dropdown):
    """
    Display an interactive widget for fitting and visualizing goethite removal from low temperature remanence data.

    This function creates an interactive interface that allows the user to select a specimen and adjust parameters
    (temperature range and polynomial degree) for fitting the goethite component in RTSIRM (Room Temperature Saturation Isothermal Remanent Magnetization) warming and cooling curves.
    The user can visually explore the effect of these parameters on the fit and resulting goethite removal, with real-time updated plots.

    Parameters
    ----------
    measurements : pandas.DataFrame
        Low temperature remanence measurement data containing temperature and magnetization information for multiple specimens.
    specimen_dropdown : ipywidgets.Dropdown
        Dropdown widget for selecting the specimen to analyze.

    Notes
    -----
    - Uses `ipywidgets` for interactive controls and `matplotlib` for plotting.
    - The temperature range for the goethite fit and the polynomial degree of the fit can be adjusted via sliders.
    - A reset button allows restoration of default parameter values.
    - Supporting functions such as `extract_mpms_data_dc` and `goethite_removal` are required for this function to operate.
    - This function is intended to be used in a Jupyter notebook or similar interactive environment.

    Returns
    -------
    None
        The function displays interactive widgets and plots for goethite removal but does not return a value.

    Examples
    --------
    >>> goethite_removal_interactive(measurements_df, specimen_dropdown)
    Displays interactive sliders and plots for fitting goethite removal to the selected specimen's data.
    """
    _check_ipywidgets()
    selected_specimen_name = specimen_dropdown.value

    fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data = extract_mpms_data_dc(measurements, selected_specimen_name)

    # Determine a fixed width for the descriptions to align the sliders
    description_width = '250px'  # Adjust this based on the longest description
    slider_total_width = '600px'  # Total width of the slider widget including the description

    description_style = {'description_width': description_width}
    slider_layout = widgets.Layout(width=slider_total_width)  # Set the total width of the slider widget

    # Update sliders to use IntRangeSlider
    temp_range_slider = widgets.IntRangeSlider(
        value=[150, 290], min=0, max=300, step=1,
        description='Geothite Fit Temperature Range (K):',
        layout=slider_layout, style=description_style
    )

    poly_deg_slider = widgets.IntSlider(
        value=2, min=1, max=3, step=1,
        description='Goethite Fit Polynomial Degree:',
        layout=slider_layout, style=description_style
    )

    # Function to reset sliders to initial values
    def reset_sliders(b):
        temp_range_slider.value = (150, 290)
        poly_deg_slider.value = 2

    # Create reset button
    reset_button = widgets.Button(description="Reset to Default Values", layout=widgets.Layout(width='200px'))
    reset_button.on_click(reset_sliders)
    
    title_label = widgets.Label(value='Adjust Parameters for ' + selected_specimen_name + ' ' + 'goethite' + ' fit')

    # Add the reset button to the UI
    ui = widgets.VBox([ 
        title_label,
        temp_range_slider, 
        poly_deg_slider,
        reset_button
    ])

    out = widgets.interactive_output(
        lambda temp_range, poly_deg: goethite_removal(
            rtsirm_warm_data, rtsirm_cool_data, 
            temp_range[0], temp_range[1],
            poly_deg
        ), {
            'temp_range': temp_range_slider,
            'poly_deg': poly_deg_slider,
        }
    )

    out.layout.height = '500px'

    display(ui, out)


def plot_mpms_ac(
        experiment,
        frequency=None,
        phase='in',
        figsize=(6, 6),
        interactive=False,
        return_figure=False,
        show_plot=True,
        legend_location='upper left'):
    """
    Plot AC susceptibility data from MPMS-X, optionally as interactive Bokeh.

    Parameters
    ----------
    experiment : pandas.DataFrame
        The experiment table from the MagIC contribution.
    frequency : float or None
        Frequency of AC measurement in Hz; None plots all frequencies.
    phase : {'in','out','both'}
        Which phase to plot.
    figsize : tuple of float
        Figure size for Matplotlib (width, height).
    interactive : bool
        If True, render with Bokeh for interactive exploration.
    return_figure : bool
        If True, return the figure object(s).
    show_plot : bool
        If True, display the plot.
    legend_location : str, default 'upper left'
        Location of the legend in Matplotlib terms.

    Returns
    -------
    fig, ax or (fig, axes) or Bokeh layout or None
    """
    bokeh_legend_location = map_legend_location(legend_location)

    if phase not in ['in', 'out', 'both']:
        raise ValueError('phase must be "in", "out", or "both"')
    freqs = ([frequency] if frequency is not None
             else experiment['meas_freq'].unique().tolist())
    if frequency is not None and frequency not in freqs:
        raise ValueError(f'frequency must be one of {freqs}')

    if interactive:
        _check_bokeh()
        tools = [
            HoverTool(tooltips=[('T', '@x'), ('χ', '@y')]),
            'pan,box_zoom,wheel_zoom,reset,save']
        n = len(freqs)
        palette = Category10[n] if n <= 10 else Category10[10]
        figs = []

        bokeh_height = int(figsize[1] * 96)

        if phase in ['in', 'out']:
            p = figure(
                title=f'AC χ ({phase} phase)',
                x_axis_label='Temperature (K)',
                y_axis_label='χ (m³/kg)',
                tools=tools,
                sizing_mode='stretch_width',
                height=bokeh_height
            )
            p.xaxis.axis_label_text_font_style = "normal"
            p.yaxis.axis_label_text_font_style = "normal"
            for i, f in enumerate(freqs):
                d = experiment[experiment['meas_freq'] == f]
                col = 'susc_chi_mass' if phase == 'in' else 'susc_chi_qdr_mass'
                color = palette[i]
                p.line(
                    d['meas_temp'], d[col],
                    legend_label=f'{f} Hz',
                    line_width=2,
                    color=color)
                p.scatter(
                    d['meas_temp'], d[col],
                    size=6,
                    alpha=0.6,
                    fill_color=color,
                    line_color=color,
                    legend_label=f'{f} Hz')
            p.legend.location = bokeh_legend_location
            p.legend.click_policy = "hide"
            figs = [p]
        else:
            p1 = figure(
                title='AC χ in phase',
                x_axis_label='Temperature (K)',
                y_axis_label='χ (m³/kg)',
                tools=tools,
                sizing_mode='stretch_width',
                height=bokeh_height
            )
            p2 = figure(
                title='AC χ out phase',
                x_axis_label='Temperature (K)',
                y_axis_label='χ (m³/kg)',
                tools=tools,
                sizing_mode='stretch_width',
                height=bokeh_height
            )
            for p in (p1, p2):
                p.xaxis.axis_label_text_font_style = "normal"
                p.yaxis.axis_label_text_font_style = "normal"
            for i, f in enumerate(freqs):
                d = experiment[experiment['meas_freq'] == f]
                color = palette[i]
                p1.line(
                    d['meas_temp'], d['susc_chi_mass'],
                    legend_label=f'{f} Hz',
                    line_width=2,
                    color=color)
                p1.scatter(
                    d['meas_temp'], d['susc_chi_mass'],
                    size=6,
                    alpha=0.6,
                    fill_color=color,
                    line_color=color,
                    legend_label=f'{f} Hz')
                p2.line(
                    d['meas_temp'], d['susc_chi_qdr_mass'],
                    legend_label=f'{f} Hz',
                    line_width=2,
                    color=color)
                p2.scatter(
                    d['meas_temp'], d['susc_chi_qdr_mass'],
                    size=6,
                    alpha=0.6,
                    fill_color=color,
                    line_color=color,
                    legend_label=f'{f} Hz')
            p1.legend.location = bokeh_legend_location
            p2.legend.location = bokeh_legend_location
            p1.legend.click_policy = p2.legend.click_policy = "hide"
            figs = [p1, p2]

        layout = gridplot([figs], sizing_mode='stretch_width')
        if show_plot:
            show(layout)
        if return_figure:
            return layout
        return None

    # static Matplotlib
    if phase in ['in', 'out']:
        fig, ax = plt.subplots(figsize=figsize)
        col = 'susc_chi_mass' if phase == 'in' else 'susc_chi_qdr_mass'
        for f in freqs:
            d = experiment[experiment['meas_freq'] == f]
            ax.plot(d['meas_temp'], d[col], 'o-', label=f'{f} Hz')
        ax.set_xlabel('Temperature (K)')
        ax.set_ylabel('χ (m³/kg)')
        ax.set_title(f'AC χ ({phase} phase)')
        ax.legend(loc=legend_location)
        if show_plot:
            plt.show()
        if return_figure:
            return fig, ax
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    for f in freqs:
        d = experiment[experiment['meas_freq'] == f]
        ax1.plot(d['meas_temp'], d['susc_chi_mass'], 'o-', label=f'{f} Hz')
        ax2.plot(d['meas_temp'], d['susc_chi_qdr_mass'], 'o-', label=f'{f} Hz')
    ax1.set_xlabel('Temperature (K)')
    ax1.set_ylabel('χ (m³/kg)')
    ax1.set_title('AC χ in phase')
    ax1.legend(loc=legend_location)
    ax2.set_xlabel('Temperature (K)')
    ax2.set_ylabel('χ (m³/kg)')
    ax2.set_title('AC χ out phase')
    ax2.legend(loc=legend_location)
    if show_plot:
        plt.show()
    if return_figure:
        return fig, (ax1, ax2)


def mpms_signal_blender(measurement_1, measurement_2, 
                        spec_1, spec_2,
                        experiments=['LP-ZFC', 'LP-FC', 'LP-CW-SIRM:LP-MC', 'LP-CW-SIRM:LP-MW'],
                        temp_col='meas_temp', moment_col='magn_mass',
                        fraction=0.5):
    '''
    function for simulating simple mixtures of MPMS dc remanence measurements using the Insitute for Rock Magnetism's
     rock magnetism bestiary data

    Parameters
    ----------
    measurement_1 : pandas.DataFrame
        MagIC formatted dataframe containing the first set of measurements.
    measurement_2 : pandas.DataFrame
        MagIC formatted dataframe containing the second set of measurements.
    spec_1 : str
        Specimen name for the first set of measurements.
    spec_2 : str
        Specimen name for the second set of measurements.
    experiments : list of str, optional
        List of experiment method codes to consider for blending. Default is
        ['LP-ZFC', 'LP-FC', 'LP-CW-SIRM:LP-MC', 'LP-CW-SIRM:LP-MW'].
    temp_col : str, optional
        Column name for temperature in the measurement dataframes. Default is 'meas_temp'.
    moment_col : str, optional
        Column name for magnetization in the measurement dataframes. Default is 'magn_mass'.
    fraction : float, optional
        Fraction of the first specimen's magnetization to blend with the second specimen's magnetization. Default is 0.5.

    Returns
    -------
    dict
        A dictionary where keys are experiment method codes and values are dictionaries containing:
    '''
    spec_1_meas = measurement_1[measurement_1['specimen']==spec_1]
    spec_2_meas = measurement_2[measurement_2['specimen']==spec_2]

    output_dict = {}

    for experiment in experiments:
        exp_1 = spec_1_meas[spec_1_meas['method_codes']==experiment]
        exp_2 = spec_2_meas[spec_2_meas['method_codes']==experiment]
        if exp_1.empty or exp_2.empty:
            continue

        T1 = exp_1[temp_col].values
        T2 = exp_2[temp_col].values
        T_min = max(T1.min(), T2.min())
        T_max = min(T1.max(), T2.max())
        n = max(len(T1), len(T2))
        T_common = np.linspace(T_min, T_max, n)

        M1 = exp_1[moment_col].values
        M2 = exp_2[moment_col].values
        # sort M1 and M2 based on sorted T1 and T2
        M1_sorted = M1[np.argsort(T1)]
        M2_sorted = M2[np.argsort(T2)]
        T1_sorted = np.sort(T1)
        T2_sorted = np.sort(T2)
        M1_interp = np.interp(T_common, T1_sorted, M1_sorted)
        M2_interp = np.interp(T_common, T2_sorted, M2_sorted)

        M_blend = fraction * M1_interp + (1 - fraction) * M2_interp
        output_dict[experiment] = {
            'T': T_common,
            'M_blend': M_blend,
        }
    return output_dict


def mpms_signal_blender_interactive(measurement_1, measurement_2, 
                                    experiments=['LP-ZFC', 'LP-FC', 'LP-CW-SIRM:LP-MC', 'LP-CW-SIRM:LP-MW'],
                                    temp_col='meas_temp', moment_col='magn_mass', 
                                    figsize=(12, 6)):
    '''
    function for making interactive blender of MPMS dc remanence measurements using the Institute for Rock Magnetism's
     rock magnetism bestiary data

    Parameters
    ----------
    measurement_1 : pandas.DataFrame
        MagIC formatted dataframe containing the first set of measurements.
    measurement_2 : pandas.DataFrame
        MagIC formatted dataframe containing the second set of measurements.    
    experiments : list of str, optional
        List of experiment method codes to consider for blending. Default is
        ['LP-ZFC', 'LP-FC', 'LP-CW-SIRM:LP-MC', 'LP-CW-SIRM:LP-MW'].
    temp_col : str, optional
        Column name for temperature in the measurement dataframes. Default is 'meas_temp'.
    moment_col : str, optional
        Column name for magnetization in the measurement dataframes. Default is 'magn_mass'.
    figsize : tuple of float, optional
        Size of the figure for plotting. Default is (12, 6).

    '''
    _check_ipywidgets()
    slider = FloatSlider(
        value=0.5, min=0, max=1, step=0.01,
        description='fraction', continuous_update=False
    )
    display(HBox([slider]))

    spec_1_dropdown = widgets.Dropdown(
        options=measurement_1['specimen'].unique(),
        description='Specimen 1:',
        disabled=False,
    )

    spec_2_dropdown = widgets.Dropdown(
        options=measurement_2['specimen'].unique(),
        description='Specimen 2:',
        disabled=False,
    )

    display(spec_1_dropdown, spec_2_dropdown)

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=figsize)
    fig.canvas.header_visible = False
    def update(*args):
        ax[0].clear()
        ax[1].clear()
        blender_result = mpms_signal_blender(
            measurement_1, measurement_2,
            spec_1_dropdown.value, spec_2_dropdown.value,
            experiments=experiments,
            temp_col=temp_col, moment_col=moment_col,
            fraction=slider.value
        )

        for experiment, data in blender_result.items():

            if 'LP-FC' in experiment:
                ax[0].plot(data['T'], data['M_blend'], marker='o', markersize=5, color='blue', alpha=0.6, label=experiment)
            elif 'LP-ZFC' in experiment:
                ax[0].plot(data['T'], data['M_blend'], marker='o', markersize=5, color='red', alpha=0.6, label=experiment)
            elif 'LP-CW-SIRM:LP-MC' in experiment:
                ax[1].plot(data['T'], data['M_blend'], marker='o', markersize=5, color='green', alpha=0.6, label=experiment)
            elif 'LP-CW-SIRM:LP-MW' in experiment:
                ax[1].plot(data['T'], data['M_blend'], marker='o', markersize=5, color='black', alpha=0.6, label=experiment)

        ax[0].set_xlabel('Temperature (K)', fontsize=12)
        ax[0].set_ylabel('Magnetization (Am$^2$/kg)', fontsize=12)
        ax[0].set_title('FC and ZFC')
        ax[0].legend()
        ax[0].grid()
        ax[1].set_xlabel('Temperature (K)', fontsize=12)
        ax[1].set_ylabel('Magnetization (Am$^2$/kg)', fontsize=12)
        ax[1].set_title('RTSIRM cycling')
        ax[1].legend()
        ax[1].grid()
        # fig.canvas.draw()
        fig.canvas.flush_events()
        plt.tight_layout()
    slider.observe(update, names='value')
    spec_1_dropdown.observe(update, names='value')
    spec_2_dropdown.observe(update, names='value')
    update()


# hysteresis functions
# ------------------------------------------------------------------------------------------------------------------

def extract_hysteresis_data(df, specimen_name):
    """
    Extracts hysteresis loop data for a specific specimen from a dataframe.

    This function filters measurements for a given specimen and returns rows
    whose MagIC method codes contain 'LP-HYS' (hysteresis loop experiments).

    Parameters:
        df (pandas.DataFrame): The dataframe containing MagIC measurement data.
        specimen_name (str): The name of the specimen to filter data for.

    Returns:
        pandas.DataFrame: Measurements for the specimen with 'LP-HYS' in
            their method codes (empty if none are present).

    Example:
        >>> hyst_data = extract_hysteresis_data(measurements_df, 'Specimen_1')
    """

    specimen_df = df[df['specimen'] == specimen_name]

    hyst_data = specimen_df[specimen_df['method_codes'].str.contains('LP-HYS', na=False)]

    return hyst_data

def plot_hysteresis_loop(field, magnetization, specimen_name, p=None, interactive=True, show_plot=True, return_figure=False, line_color='grey', line_width=1, label='', legend_location='bottom_right'):
    '''
    function to plot a hysteresis loop

    Parameters
    ----------
    field : numpy array or list
        hysteresis loop field values
    magnetization : numpy array or list
        hysteresis loop magnetization values

    Returns
    -------
    p : bokeh.plotting.figure
    
    '''
    _check_bokeh()
    assert len(field) == len(magnetization), 'Field and magnetization arrays must be the same length'
    if interactive:
        if p is None:
            p = figure(title=f'{specimen_name} hysteresis loop',
                    x_axis_label='Field (T)',
                    y_axis_label='Magnetization (Am\u00B2/kg)',
                    width=600,
                    height=600, aspect_ratio=1)
            p.axis.axis_label_text_font_size = '12pt'
            p.axis.axis_label_text_font_style = 'normal'
            p.title.text_font_size = '14pt'
            p.title.text_font_style = 'bold'
            p.title.align = 'center'
            p.line(field, magnetization, line_width=line_width, color=line_color, legend_label=label)
            p.legend.click_policy="hide"
            p.legend.location = legend_location
        else:
            p.line(field, magnetization, line_width=line_width, color=line_color, legend_label=label)
            p.legend.location = legend_location
        
        if show_plot:
            show(p)
        if return_figure:
            return p
        return None
    
    # static Matplotlib
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(field, magnetization, color=line_color, linewidth=line_width, label=label)
    ax.set_title(f'{specimen_name} hysteresis loop')
    ax.set_xlabel('Field (T)')
    ax.set_ylabel('Magnetization (Am²/kg)')
    ax.legend(loc=legend_location)
    ax.grid(True)
    if show_plot:
        plt.show()
    if return_figure:
        return fig, ax
    return None

def collapse_hysteresis_field_plateaus(field, magnetization):
    """Average consecutive repeated field steps into a single point."""
    field = np.asarray(field, dtype=float)
    magnetization = np.asarray(magnetization, dtype=float)

    if field.size == 0:
        return field, magnetization

    collapsed_field = []
    collapsed_magnetization = []
    start = 0

    for index in range(1, len(field) + 1):
        if index == len(field) or field[index] != field[start]:
            collapsed_field.append(field[start])
            collapsed_magnetization.append(np.mean(magnetization[start:index]))
            start = index

    return np.asarray(collapsed_field, dtype=float), np.asarray(collapsed_magnetization, dtype=float)

def find_hysteresis_turning_point(field):
    """Find the single loop reversal, tolerating repeated plateaus and minor field glitches.

    Returns the index of the last point of the first field sweep, such that
    field[:index+1] is the first branch and field[index+1:] is the second
    branch. Zero field steps (plateaus from repeated field values) are ignored
    when detecting the reversal, and if field glitches produce multiple sign
    changes, the reversal closest to the global field extremum opposite the
    initial sweep direction is chosen.
    """
    field = np.asarray(field, dtype=float)
    if field.size < 3:
        raise ValueError('At least three field steps are required to split a hysteresis loop')

    field_diff = np.diff(field)
    nonzero_indices = np.where(field_diff != 0)[0]
    if nonzero_indices.size == 0:
        raise ValueError('Applied field does not vary and cannot be split into loop branches')

    diff_sign = np.sign(field_diff[nonzero_indices])
    # sign changes between consecutive non-zero field steps mark reversals;
    # the turning point is the last index of the sweep ending at the reversal
    sign_changes = np.where(diff_sign[:-1] * diff_sign[1:] < 0)[0]
    if sign_changes.size == 0:
        raise ValueError('No turning point found in the applied field. The data may not be a hysteresis loop.')
    candidates = nonzero_indices[sign_changes] + 1
    if candidates.size == 1:
        return int(candidates[0])

    initial_direction = np.sign(np.median(diff_sign[:min(10, len(diff_sign))]))
    if initial_direction == 0:
        initial_direction = diff_sign[0]

    extremum_index = int(np.argmin(field) if initial_direction < 0 else np.argmax(field))
    return int(candidates[np.argmin(np.abs(candidates - extremum_index))])

def build_symmetric_hysteresis_grid(upper_branch, lower_branch):
    """Build a symmetric field grid over the overlap shared by the two loop branches."""
    upper_field = np.asarray(upper_branch[0], dtype=float)
    lower_field = np.asarray(lower_branch[0], dtype=float)

    branch_steps = np.concatenate([
        np.abs(np.diff(upper_field)),
        np.abs(np.diff(lower_field)),
    ])
    branch_steps = branch_steps[branch_steps > 0]
    if branch_steps.size == 0:
        raise ValueError('Cannot determine a non-zero field step for hysteresis gridding')

    field_step = np.median(branch_steps)
    max_field = min(
        np.max(upper_field),
        np.max(lower_field),
        np.abs(np.min(upper_field)),
        np.abs(np.min(lower_field)),
    )
    if max_field <= 0:
        raise ValueError('Hysteresis branches do not overlap symmetrically about zero field')

    positive_field = np.arange(max_field, 0, -field_step, dtype=float)
    if positive_field.size == 0:
        positive_field = np.asarray([max_field], dtype=float)

    upper_grid = np.concatenate([positive_field, -positive_field[::-1]])
    lower_grid = upper_grid[::-1]
    return upper_grid, lower_grid

def sanitize_hysteresis_inputs(field, magnetization, drop_nonfinite=True):
    """Coerce hysteresis loop inputs into clean float arrays for processing.

    This helper makes the processing functions usable with data from any
    source: MagIC measurement table columns (including ones read as text),
    plain Python lists, or arrays exported from instrument software.

    Parameters
    ----------
    field : array_like
        Applied field values. Expected in tesla: the chi_HF unit conversions
        in `linear_HF_fit`, `hyst_slope_correction`, and the nonlinear fits
        assume tesla, so a warning is printed if the values appear to be in
        mT or Oe (max |field| > 20).
    magnetization : array_like
        Magnetization or moment values, in any unit that is consistent
        across the loop (mass-normalized Am2/kg matches MagIC conventions).
    drop_nonfinite : bool, optional
        If True (default), measurement pairs where either value is NaN or
        infinite are dropped with a printed report. If False, a ValueError
        is raised when non-finite values are present.

    Returns
    -------
    field, magnetization : numpy.ndarray
        Equal-length float arrays with only finite values.
    """
    try:
        field = np.asarray(field, dtype=float)
        magnetization = np.asarray(magnetization, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError('Field and magnetization values must be numeric '
                         f'(or numeric strings): {error}')
    if field.ndim != 1 or magnetization.ndim != 1:
        raise ValueError('Field and magnetization must be one-dimensional sequences')
    if field.shape != magnetization.shape:
        raise ValueError('Field and magnetization arrays must be the same length')

    finite = np.isfinite(field) & np.isfinite(magnetization)
    if not finite.all():
        n_dropped = int(np.sum(~finite))
        if not drop_nonfinite:
            raise ValueError(f'{n_dropped} measurement(s) have non-finite field '
                             'or magnetization values')
        print(f'-W- dropping {n_dropped} measurement(s) with non-finite field '
              'or magnetization values')
        field = field[finite]
        magnetization = magnetization[finite]

    if field.size < 10:
        raise ValueError('At least 10 finite measurements are required to '
                         'process a hysteresis loop')

    max_field = np.max(np.abs(field))
    if max_field > 20:
        print(f'-W- maximum |field| is {max_field:g}, which suggests the field '
              'values are not in tesla (e.g. mT or Oe); the high-field '
              'susceptibility unit conversions assume tesla')

    return field, magnetization

def split_hysteresis_loop(field, magnetization):
    '''
    function to split a hysteresis loop into upper and lower branches
        at the reversal of the applied field sweep

    The loop reversal is located with `find_hysteresis_turning_point`, which
    tolerates repeated field plateaus and minor field glitches. Loops measured
    in either sweep order are supported: the branch measured from the positive
    field extreme downward is returned as the upper branch regardless of
    whether it was measured first or second.

    Parameters
    ----------
    field : numpy array or list
        hysteresis loop field values
    magnetization : numpy array or list
        hysteresis loop magnetization values

    Returns
    -------
    upper_branch : list
        [field, magnetization] for the upper branch, in ascending field order
    lower_branch : list
        [field, magnetization] for the lower branch, in ascending field order
    '''
    assert len(field) == len(magnetization), 'Field and magnetization arrays must be the same length'
    field = np.asarray(field, dtype=float)
    magnetization = np.asarray(magnetization, dtype=float)

    turning_point = find_hysteresis_turning_point(field)
    first_branch = [field[:turning_point+1], magnetization[:turning_point+1]]
    second_branch = [field[turning_point+1:], magnetization[turning_point+1:]]

    if field[0] > field[turning_point]:
        # sweep starts at the positive extreme: the first segment is the
        # descending upper branch; reverse it into ascending field order
        upper_branch = [first_branch[0][::-1], first_branch[1][::-1]]
        lower_branch = second_branch
    else:
        # sweep starts at the negative extreme: the first segment is the
        # ascending lower branch and the second is the descending upper branch
        lower_branch = first_branch
        upper_branch = [second_branch[0][::-1], second_branch[1][::-1]]

    return upper_branch, lower_branch

def grid_hysteresis_loop(field, magnetization):
    '''
    function to grid a hysteresis loop into a regular grid
        with grid intervals equal to the average field step size calculated from the data

    Parameters
    ----------
    field : numpy array or list
        hysteresis loop field values
    magnetization : numpy array or list
        hysteresis loop magnetization values

    Returns
    -------
    grid_field : numpy array
        gridded field values
    grid_magnetization : numpy array
        gridded magnetization values
    '''
    assert len(field) == len(magnetization), 'Field and magnetization arrays must be the same length'
    field = np.asarray(field, dtype=float)
    magnetization = np.asarray(magnetization, dtype=float)
    if not (np.isfinite(field).all() and np.isfinite(magnetization).all()):
        raise ValueError('Non-finite field or magnetization values present; '
                         'clean the inputs first (see sanitize_hysteresis_inputs)')

    upper_branch, lower_branch = split_hysteresis_loop(field, magnetization)

    # average any exactly repeated field steps within each branch (e.g.
    # instrument plateaus at the loop tips) so duplicate fields do not enter
    # the interpolation; small non-monotonic field glitches are not repaired
    # here and np.interp will locally smooth over them
    upper_branch = collapse_hysteresis_field_plateaus(upper_branch[0], upper_branch[1])
    lower_branch = collapse_hysteresis_field_plateaus(lower_branch[0], lower_branch[1])

    upper_field, lower_field = build_symmetric_hysteresis_grid(upper_branch, lower_branch)
    grid_field = np.concatenate([upper_field, lower_field])
    
    upper_branch_itp = np.interp(upper_field, upper_branch[0], upper_branch[1])
    lower_branch_itp = np.interp(lower_field, lower_branch[0], lower_branch[1])
    grid_magnetization = np.concatenate([upper_branch_itp, lower_branch_itp])

    return grid_field, grid_magnetization

def ANOVA(xs, ys):
    '''
    ANOVA statistics for linear regression
    
    Parameters
    ----------
    xs : numpy array
        x values
    ys : numpy array
        y values

    Returns
    -------
    results : dict
        dictionary of the results of the ANOVA calculation
        and intermediate statistics for the ANOVA calculation

    '''

    xs = np.array(xs)
    ys = np.array(ys)

    ys_mean = np.mean(ys)

    # fit the gridded data by a straight line
    slope, intercept = np.polyfit(xs, ys, 1)

    # AVOVA calculation
    # total sum of squares for the dependent variable (magnetization)
    SST = np.sum((ys - ys_mean)**2)

    # sum of squares due to regression
    SSR = np.sum((slope * xs + intercept - ys_mean)**2)
    
    # the remaining unexplained variation (noise and lack of fit)
    SSD = np.sum((ys - (slope * xs + intercept)) ** 2)
    R_squared = SSR/SST

    results = {'slope':slope,
                'intercept':intercept,
                'SST':SST,
                'SSR':SSR,
                'SSD':SSD,
                'R_squared': R_squared}
    
    return results

def hyst_linearity_test(grid_field, grid_magnetization):
    '''
    function for testing the linearity of a hysteresis loop

    Parameters
    ----------
    grid_field : numpy array
        gridded field values
    grid_magnetization : numpy array
        gridded magnetization values

    Returns
    -------
    results : dict
        dictionary of the results of the linearity test
        and intermediate statistics for the ANOVA calculation
    '''
    grid_field = np.array(grid_field)
    grid_magnetization = np.array(grid_magnetization)

    upper_branch, lower_branch = split_hysteresis_loop(grid_field, grid_magnetization)

    anova_results = ANOVA(grid_field, grid_magnetization)

    # fit the gridded data by a straight line
    slope, intercept = anova_results['slope'], anova_results['intercept']

    # AVOVA calculation
    # total sum of squares for the dependent variable (magnetization)
    SST = anova_results['SST']

    # sum of squares due to regression
    SSR = anova_results['SSR']
    
    # the remaining unexplained variation (noise and lack of fit)
    SSD = anova_results['SSD']

    R_squared = anova_results['R_squared']

    # invert the lower branch to match the upper branch
    # and calculate the differences between the upper and the inverted lower branch
    # for any loop shifts and drift that are due to noise alone
    SSPE = np.sum((upper_branch[1] - (-lower_branch[1][::-1])) ** 2)  / 2

    # calculate the lack of fit statistic
    SSLF = SSD - SSPE

    # mean square pure error
    MSPE = SSPE / (len(grid_field)  / 2)

    # mean square error due to lack of fit
    MSLF = SSLF / (len(grid_field)/2 - 2)

    # mean squares due to regression
    MSR = SSR 

    # mean squares due to noise
    MSD = SSD / (len(grid_field) - 2)

    # F-ratio for the linear component
    FL = MSR / MSD

    # F-ratio for the non-linear component
    FNL = MSLF / MSPE

    results = {
        'SST': float(SST),
        'SSR': float(SSR),
        'SSD': float(SSD),
        'R_squared': float(R_squared),
        'SSPE': float(SSPE),
        'SSLF': float(SSLF),
        'MSPE': float(MSPE),
        'MSLF': float(MSLF),
        'MSR': float(MSR),
        'MSD': float(MSD),
        'FL': float(FL),
        'FNL': float(FNL),
        'slope': float(slope),
        'intercept': float(intercept),
        'loop_is_linear': bool(FNL < 1.25),
    }

    return results

def linefit(xarr, yarr):
    """
    Perform a simple linear regression (least squares fit) on two arrays.

    Parameters
    ----------
    xarr : array_like
        Array of x-values (independent variable).
    yarr : array_like
        Array of y-values (dependent variable), must be the same shape as `xarr`.

    Returns
    -------
    intercept : float
        The intercept of the best-fit line.
    slope : float
        The slope of the best-fit line.
    r2 : float
        The coefficient of determination (R²), a measure of how well the regression line fits the data.
        R² = 1 indicates a perfect fit, lower values indicate a poorer fit.

    Examples
    --------
    >>> x = [0, 1, 2, 3, 4]
    >>> y = [1, 3, 5, 7, 9]
    >>> intercept, slope, r2 = linefit(x, y)
    >>> print(f"Intercept: {intercept:.2f}, Slope: {slope:.2f}, R^2: {r2:.2f}")
    Intercept: 1.00, Slope: 2.00, R^2: 1.00
    """
    xarr = np.asarray(xarr)
    yarr = np.asarray(yarr)
    
    # Fit a line y = slope * x + intercept
    slope, intercept = np.polyfit(xarr, yarr, 1)

    # Predict y using the fitted line
    y_pred = intercept + slope * xarr

    # Total sum of squares
    ss_tot = np.sum((yarr - np.mean(yarr))**2)

    # Residual sum of squares
    ss_res = np.sum((yarr - y_pred)**2)

    # R^2 score
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1

    return intercept, slope, r2

def branch_symmetry_mismatch(loop_fields, loop_moments, H_shift=0.0, M_shift=None,
                              low_field_fraction=0.35, weight_power=4):
    """Measure branch inversion symmetry with optional low-field weighting."""
    corrected_fields = np.asarray(loop_fields, dtype=float) - H_shift
    corrected_moments = np.asarray(loop_moments, dtype=float)

    upper_branch, lower_branch = split_hysteresis_loop(corrected_fields, corrected_moments)
    upper_field = np.asarray(upper_branch[0], dtype=float)
    upper_moment = np.asarray(upper_branch[1], dtype=float)
    lower_field = np.asarray(lower_branch[0], dtype=float)
    lower_moment = np.asarray(lower_branch[1], dtype=float)

    mirror_field = -upper_field
    valid = (mirror_field >= np.min(lower_field)) & (mirror_field <= np.max(lower_field))
    if not np.any(valid):
        raise ValueError('Loop branches do not overlap after applying the proposed field shift')

    overlap_field = upper_field[valid]
    overlap_upper_moment = upper_moment[valid]
    overlap_lower_moment = np.interp(-overlap_field, lower_field, lower_moment)

    max_field = np.max(np.abs(overlap_field))
    field_scale = max(low_field_fraction * max_field, np.finfo(float).eps)
    weights = 1.0 / (1.0 + (np.abs(overlap_field) / field_scale) ** weight_power)

    offset_samples = (overlap_upper_moment + overlap_lower_moment) / 2.0
    if M_shift is None:
        M_shift = np.average(offset_samples, weights=weights)

    mismatch = overlap_upper_moment + overlap_lower_moment - 2.0 * M_shift
    weighted_rms = np.sqrt(np.average(mismatch ** 2, weights=weights))

    return {
        'field': overlap_field,
        'mismatch': mismatch,
        'weights': weights,
        'weighted_rms': float(weighted_rms),
        'M_shift': float(M_shift),
    }

def loop_H_off(loop_fields, loop_moments, H_shift):
    """
    Estimate the vertical shift (M_shift) and symmetry (R²) of a magnetic hysteresis loop after applying a horizontal field shift.

    This function shifts the field data by a specified amount, finds symmetrically equivalent points in the second half of the loop,
    and performs a linear regression between the original and reflected/negated data. It then estimates the vertical offset (M_shift)
    based on the intercept of the regression and returns additional regression results.

    Parameters
    ----------
    loop_fields : array_like
        Array of magnetic field values for the hysteresis loop.
    loop_moments : array_like
        Array of corresponding magnetic moment values.
    H_shift : float
        Horizontal (field) shift to apply to the loop_fields before symmetry calculation.

    Returns
    -------
    result : dict
        Dictionary containing:
            - 'slope': float, slope of the linear regression between the original and reflected moments.
            - 'M_shift': float, estimated vertical shift (half the regression intercept).
            - 'r2': float, coefficient of determination (R²) for the regression, indicating symmetry.

    Notes
    -----
    - The function is typically used to estimate vertical offsets and assess symmetry in magnetic hysteresis loops.
    - Returns zeros if not enough symmetrical points are found for regression.

    Examples
    --------
    >>> res = loop_H_off(fields, moments, H_shift=10)
    >>> print(res['M_shift'], res['r2'])
    """
    n = len(loop_fields)

    # Apply horizontal shift
    loop_fields = loop_fields - H_shift

    # Define bounds for symmetrical comparison
    min2 = np.min(loop_fields)
    max2 = np.max(loop_fields)
    min1 = -max2
    max1 = -min2

    n1 = n // 2
    i2 = 0  # Python uses 0-based indexing
    x1 = []
    y1 = []

    for i in range(n1, n):
        x = loop_fields[i]
        if min1 < x < max1:
            while -loop_fields[i2] < x and i2 < n - 1:
                i2 += 1
            if i2 > 0:
                dx = (-loop_fields[i2] - x) / (-loop_fields[i2] + loop_fields[i2 - 1])
                dy = dx * (-loop_moments[i2] + loop_moments[i2 - 1])
                y = -loop_moments[i2] - dy
                x1.append(loop_moments[i])
                y1.append(-y)

    if len(x1) < 2:
        return {'slope': 0.0, 'M_shift': 0.0, 'r2': 0.0}

    intercept, slope, r2 = linefit(x1, y1)
    M_shift = intercept / 2

    result = {'slope': slope, 'M_shift': M_shift, 'r2': r2}
    return result

def loop_Hshift_brent(loop_fields, loop_moments, shift_bound_fraction=0.1):
    """
    Optimize the horizontal (field) shift of a magnetic hysteresis loop using Brent's method to maximize symmetry.

    This function determines the optimal horizontal field shift (H_shift) to apply to a hysteresis loop,
    such that the R² value (symmetry) of the loop, as calculated by `loop_H_off`, is maximized.
    It uses the Brent optimization algorithm to efficiently search for the H_shift that gives the highest R².
    The function returns the optimal R², the corresponding field shift, and the vertical offset (M_shift) at this position.

    Parameters
    ----------
    loop_fields : array_like
        Array of magnetic field values for the hysteresis loop.
    loop_moments : array_like
        Array of corresponding magnetic moment values.

    Returns
    -------
    opt_r2 : float
        The maximum R² value achieved by shifting the loop.
    opt_H_off : float
        The optimal horizontal (field) shift applied to maximize symmetry.
    opt_M_off : float
        The estimated vertical shift (M_shift) at the optimal field shift.

    Notes
    -----
    - Uses Brent's method for optimization via `scipy.optimize.minimize_scalar` with a bracket based on the loop field range.
    - Calls `loop_H_off` to compute symmetry and vertical shift for each candidate field shift.
    - Useful for correcting field and moment offsets in hysteresis loop analysis.

    Examples
    --------
    >>> r2, H_off, M_off = loop_Hshift_brent(fields, moments)
    >>> print(f"Optimal field shift: {H_off:.2f}, R²: {r2:.3f}, M_shift: {M_off:.3e}")
    """

    def objective(H_shift):
        return -loop_H_off(loop_fields, loop_moments, H_shift)['r2']

    shift_bound = shift_bound_fraction * np.max(np.abs(loop_fields))
    if shift_bound == 0:
        return 0.0, 0.0, 0.0

    coarse_grid = np.linspace(-shift_bound, shift_bound, 41)
    coarse_scores = np.asarray([loop_H_off(loop_fields, loop_moments, shift)['r2'] for shift in coarse_grid])
    best_index = int(np.argmax(coarse_scores))
    left_index = max(best_index - 1, 0)
    right_index = min(best_index + 1, len(coarse_grid) - 1)

    if left_index == right_index:
        opt_H_off = float(coarse_grid[best_index])
    else:
        result = minimize_scalar(
            objective,
            bounds=(float(coarse_grid[left_index]), float(coarse_grid[right_index])),
            method='bounded',
            options={'xatol': 1e-6},
        )
        opt_H_off = float(result.x)

    opt_shift = loop_H_off(loop_fields, loop_moments, opt_H_off)
    opt_r2 = opt_shift['r2']
    opt_M_off = opt_shift['M_shift']

    return opt_r2, opt_H_off, opt_M_off

def loop_Hshift_weighted(loop_fields, loop_moments, low_field_fraction=0.35,
                         shift_bound_fraction=0.1, weight_power=4):
    """Optimize loop centering using a low-field-weighted inversion-symmetry mismatch."""
    loop_fields = np.asarray(loop_fields, dtype=float)
    loop_moments = np.asarray(loop_moments, dtype=float)

    shift_bound = shift_bound_fraction * np.max(np.abs(loop_fields))
    if shift_bound == 0:
        mismatch = branch_symmetry_mismatch(
            loop_fields,
            loop_moments,
            low_field_fraction=low_field_fraction,
            weight_power=weight_power,
        )
        return mismatch['weighted_rms'], 0.0, mismatch['M_shift'], mismatch

    def objective(H_shift):
        return branch_symmetry_mismatch(
            loop_fields,
            loop_moments,
            H_shift=H_shift,
            low_field_fraction=low_field_fraction,
            weight_power=weight_power,
        )['weighted_rms']

    result = minimize_scalar(
        objective,
        bounds=(-shift_bound, shift_bound),
        method='bounded',
        options={'xatol': 1e-6},
    )
    opt_H_off = float(result.x)
    mismatch = branch_symmetry_mismatch(
        loop_fields,
        loop_moments,
        H_shift=opt_H_off,
        low_field_fraction=low_field_fraction,
        weight_power=weight_power,
    )
    return mismatch['weighted_rms'], opt_H_off, mismatch['M_shift'], mismatch

def calc_Q(H, M, type='Q'):
    """
    Calculate the quality factor (Q) for a magnetic hysteresis loop.

    The Q factor is a logarithmic measure (base 10) of the signal-to-noise ratio for a
    hysteresis loop, following Jackson and Solheid (2010): the upper and inverted lower
    branches are treated as replicate measurements, so their mean squared moment relative
    to the mean squared mismatch between them (the err(H) curve) quantifies signal/noise.
    Q = log10(s/n); loops with Q >= 2 have small deviations from inversion symmetry while
    loops with Q below ~0.3 (s/n ~ 2) are too noisy for meaningful parameter estimation.
    The quality factor of the ferromagnetic component (Q_f of Jackson and Solheid, 2010)
    is obtained by calling this function on the slope-corrected loop.

    The calculation can be performed in two modes:
        - 'Q': Uses the mean squared magnetization of both the upper and lower branches.
        - 'Qf': Uses only the upper branch.

    Parameters
    ----------
    H : array_like
        Array of applied magnetic field values.
    M : array_like
        Array of measured magnetization (moment) values, corresponding to `H`.
    type : {'Q', 'Qf'}, optional
        Type of Q calculation to perform:
            - 'Q' (default): Uses both upper and lower branches of the loop.
            - 'Qf': Uses only the upper branch.

    Returns
    -------
    M_sn : float
        The calculated signal-to-noise ratio (before applying the logarithm).
    Q : float
        The quality factor, defined as log10(M_sn).

    Notes
    -----
    - The function splits the hysteresis loop into upper and lower branches using `split_hysteresis_loop`.
    - For type 'Q', the numerator is the average of the sum of squares of the upper and lower branches; for 'Qf', only the upper branch is used.
    - The denominator is the sum of squares of err(H), the mismatch between the upper branch
      and the inverted lower branch, so M_sn is equivalent to the 1/(1 - R^2) signal/noise
      measure of Jackson and Solheid (2010, equation 3).
    - Higher Q values indicate a higher signal-to-noise ratio in the hysteresis loop data.

    Examples
    --------
    >>> H = np.linspace(-1, 1, 200)
    >>> M = np.tanh(3 * H) + 0.05 * np.random.randn(200)
    >>> M_sn, Q = calc_Q(H, M, type='Q')
    >>> print(f"Signal-to-noise ratio: {M_sn:.3f}, Q: {Q:.2f}")
    """
    assert type in ['Q', 'Qf'], 'type must be either Q or Qf'
    H = np.array(H)
    M = np.array(M)
    upper_branch, lower_branch = split_hysteresis_loop(H, M)
    Me = upper_branch[1] + lower_branch[1][::-1]
    # the square root follows the convention of the IRM software and HystLab
    # (Paterson et al., 2018, equation 4): Q = log10(1/sqrt(1 - R^2)); the
    # equation as printed in Jackson and Solheid (2010) omits the square root
    # but their reported values include it (see Paterson et al., 2018)
    if type == 'Q':
        M_sn = np.sqrt((np.sum(upper_branch[1]**2) + np.sum(lower_branch[1][::-1]**2))/2/np.sum(Me**2))
    elif type == 'Qf':
        M_sn = np.sqrt(np.sum(upper_branch[1]**2)/np.sum(Me**2))

    Q = np.log10(M_sn)
    return M_sn, Q

def hyst_loop_centering(grid_field, grid_magnetization):
    '''
    function for finding the optimum applied field offset value for minimizing a linear fit through 
        the Me based on the R2 value. The idea is maximizing the residual noise in the Me gives the best centered loop. 

    Parameters
    ----------
    grid_field : numpy array
        gridded field values
    grid_magnetization : numpy array
        gridded magnetization values

    Returns
    -------
    opt_H_offset : float
        optimized applied field offset value for the loop
    opt_M_offset : float
        calculated magnetization offset value for the loop based on the optimized applied field offset
        (intercept of the fitted line using the upper branch and the inverted and optimally offsetted lower branch)
    R_squared : float
        R-squared value of the linear fit between the upper branch and the inverted and offsetted lower branch

    '''
    grid_field = np.array(grid_field)
    grid_magnetization = np.array(grid_magnetization)
    R_squared, H_offset, M_offset = loop_Hshift_brent(grid_field, grid_magnetization)

    # re-gridding after offset correction to ensure symmetry
    centered_H, centered_M = grid_hysteresis_loop(grid_field-H_offset, grid_magnetization-M_offset)

    # quality factor from the offset-corrected loop (Jackson and Solheid, 2010,
    # section 3: Q reflects noise and drift after the effects of loop offsets
    # are removed; HystLab likewise computes Q on the offset-corrected curves).
    # Computing Q on the uncorrected loop would let a loop offset depress Q
    # below the decision-tree gate that decides whether to apply the offset
    # correction itself.
    M_sn, Q = calc_Q(centered_H, centered_M)

    results = {'centered_H':centered_H, 
               'centered_M': centered_M, 
               'opt_H_offset':float(H_offset), 
               'opt_M_offset':float(M_offset), 
               'R_squared':float(R_squared), 
               'M_sn':float(M_sn), 
               'Q':float(Q),
               }
    return results

def hyst_loop_centering_iterative(grid_field, grid_magnetization, hf_cutoff=0.8,
                                  low_field_fraction=0.35, shift_bound_fraction=0.1,
                                  weight_power=4, max_iterations=5,
                                  field_tolerance=1e-5, moment_tolerance=1e-8):
    """
    Center a hysteresis loop by iterating between provisional slope removal and offset fitting.

    The routine alternates between fitting a provisional high-field slope and optimizing horizontal
    and vertical offsets on the residual loop using a low-field-weighted inversion-symmetry metric.
    This is designed for weak ferromagnetic loops superimposed on a strong linear background.
    """
    centered_H, centered_M = grid_hysteresis_loop(grid_field, grid_magnetization)
    total_H_offset = 0.0
    total_M_offset = 0.0
    iteration_history = []
    provisional_slope = 0.0
    symmetry_score = np.nan

    for iteration in range(max_iterations):
        try:
            provisional_slope, _ = linear_HF_fit(centered_H, centered_M, HF_cutoff=hf_cutoff)
        except Exception:
            provisional_slope = 0.0

        ferro_like_M = hyst_slope_correction(centered_H, centered_M, provisional_slope)
        symmetry_score, delta_H, delta_M, mismatch = loop_Hshift_weighted(
            centered_H,
            ferro_like_M,
            low_field_fraction=low_field_fraction,
            shift_bound_fraction=shift_bound_fraction,
            weight_power=weight_power,
        )

        centered_H, centered_M = grid_hysteresis_loop(centered_H - delta_H, centered_M - delta_M)
        total_H_offset += delta_H
        total_M_offset += delta_M
        iteration_history.append({
            'iteration': iteration + 1,
            'provisional_slope': float(provisional_slope),
            'delta_H_offset': float(delta_H),
            'delta_M_offset': float(delta_M),
            'symmetry_score': float(symmetry_score),
            'low_field_fraction': float(low_field_fraction),
            'matched_points': int(len(mismatch['field'])),
        })

        if abs(delta_H) <= field_tolerance and abs(delta_M) <= moment_tolerance:
            break

    M_sn, Q = calc_Q(centered_H, centered_M)
    results = {
        'centered_H': centered_H,
        'centered_M': centered_M,
        'opt_H_offset': float(total_H_offset),
        'opt_M_offset': float(total_M_offset),
        'M_sn': float(M_sn),
        'Q': float(Q),
        'provisional_slope': float(provisional_slope),
        'symmetry_score': float(symmetry_score),
        'iterations': iteration_history,
        'method': 'iterative_low_field_weighted',
    }
    return results

def linear_HF_fit(field, magnetization, HF_cutoff=0.8):
    '''
    function to fit a linear function to the high field portion of a hysteresis loop

    Parameters
    ----------
    field : numpy array or list
        raw hysteresis loop field values
    magnetization : numpy array or list
        raw hysteresis loop magnetization values

    Returns
    -------
    chi_HF : float
        high-field susceptibility of the paramagnetic/diamagnetic contribution
        in SI units (the raw fitted slope in field units of Tesla multiplied
        by mu_0 = 4*pi*1e-7); `hyst_slope_correction` performs the inverse
        conversion when removing this contribution from a loop
    intercept : float
        y-intercept of the linear fit
        can be interpreted to be the saturation magnetization of the ferromagnetic component
    '''
    assert len(field) == len(magnetization), 'Field and magnetization arrays must be the same length'
    assert HF_cutoff > 0 and HF_cutoff < 1, 'Portion must be between 0 and 1'

    # adopting IRM's max field cutoff at 97% of the max field
    max_field_cutoff = 0.97
    
    field = np.array(field)
    magnetization = np.array(magnetization)

    # filter for the high field portion of each branch

    high_field_index = np.where((np.abs(field) >= HF_cutoff*np.max(np.abs(field))) & (np.abs(field) <= max_field_cutoff*np.max(np.abs(field))))[0]

    # invert points in the negative high fields
    high_field = np.abs(field[high_field_index])
    high_field_magnetization = np.where(field[high_field_index] >= 0, magnetization[high_field_index], -magnetization[high_field_index])

    # the slope would be the paramagnetic/diamagnetic susceptibility
    # the y-intercept would be the Ms value (saturation magnetization of the ferromagnetic component)
    slope, intercept = np.polyfit(high_field, high_field_magnetization, 1)
    chi_HF = slope * (4*np.pi/1e7)
    return chi_HF, intercept

def hyst_slope_correction(grid_field, grid_magnetization, chi_HF):
    '''
    function for subtracting the paramagnetic/diamagnetic slope from a hysteresis loop
         the input should be gridded field and magnetization values

    Parameters
    ----------
    grid_field : numpy array
        gridded field values
    grid_magnetization : numpy array
        gridded magnetization values
    chi_HF : float
        X_HF 

    Returns
    -------
    grid_magnetization_ferro: numpy array
        corrected ferromagnetic component of the magnetization
    '''
    slope = chi_HF / (4*np.pi/1e7)
    assert len(grid_field) == len(grid_magnetization), 'Field and magnetization arrays must be the same length'
    
    grid_field = np.array(grid_field)
    grid_magnetization = np.array(grid_magnetization)

    grid_magnetization_ferro = grid_magnetization - slope*grid_field

    return grid_magnetization_ferro

def find_y_crossing(x, y, y_target=0.0):
    """
    Finds the x-value where y crosses a given y_target, taking the first
    crossing encountered in array order. Uses linear interpolation between
    adjacent points that bracket y_target.

    Parameters:
        x (array-like): x-values
        y (array-like): y-values
        y_target (float): y-value at which to find crossing (default: 0)

    Returns:
        x_cross (float or None): interpolated x at y = y_target for the first
            crossing in array order, or None if not found
    """
    x = np.asarray(x)
    y = np.asarray(y)

    for i in range(len(x) - 1):
        y0, y1 = y[i], y[i + 1]
        if (y0 - y_target) * (y1 - y_target) < 0:  # sign change => crossing
            x0, x1 = x[i], x[i + 1]
            # Linear interpolation to find x at y = y_target
            x_cross = x0 + (y_target - y0) * (x1 - x0) / (y1 - y0)
            return x_cross

    return None 

def calc_Mr_Mrh_Mih_Brh(grid_field, grid_magnetization):
    '''
    function to calculate the Mrh and Mih values from a hysteresis loop

    Parameters
    ----------
    grid_field : numpy array
        gridded field values
    grid_magnetization : numpy array
        gridded magnetization values

    Returns
    -------
    H : numpy array
        field values of the upper branch (the two branches should have the same field values)
    Mr : float
        remanent magnetization (Mrh interpolated at zero field)
    Mrh : numpy array
        remanent hysteretic magnetization, (upper - lower)/2
    Mih : numpy array
        induced hysteretic magnetization, (upper + lower)/2
    Me : numpy array
        error curve err(H), the mismatch between the upper branch and the inverted lower branch
    Brh : float
        median field of Mrh (field at which Mrh falls to half of Mr)

    '''
    # calculate Mrh by subtracting the upper and lower branches of a hysteresis loop
    grid_field = np.array(grid_field)
    grid_magnetization = np.array(grid_magnetization)

    upper_branch, lower_branch = split_hysteresis_loop(grid_field, grid_magnetization)

    Mrh = (upper_branch[1] - lower_branch[1])/2
    Mih = (upper_branch[1] + lower_branch[1])/2
    Me = upper_branch[1] + lower_branch[1][::-1]

    H = upper_branch[0]
    Mr = np.interp(0, H, Mrh)

    # Brh is the field corresponding to the m=Mr/2
    pos_H = H[np.where(H > 0)]
    pos_Mrh = Mrh[np.where(H > 0)]
    neg_H = H[np.where(H < 0)]
    neg_Mrh = Mrh[np.where(H < 0)]
    Brh_pos = find_y_crossing(pos_H, pos_Mrh, Mr/2)
    Brh_neg = find_y_crossing(neg_H, neg_Mrh, Mr/2)
    Brh = np.abs((Brh_pos - Brh_neg)/2)

    return H, Mr, Mrh, Mih, Me, Brh

def calc_Bc(H, M):
    '''
    function for calculating the coercivity of the ferromagnetic component of a hysteresis loop
        the final Bc value is calculated as the average of the positive and negative Bc values

    Parameters
    ----------
    H : numpy array
        field values
    M : numpy array
        magnetization values

    Returns
    -------
    Bc : float
        coercivity of the ferromagnetic component of the hysteresis loop
    '''
    upper_branch, lower_branch = split_hysteresis_loop(H, M)

    upper_Bc = find_y_crossing(upper_branch[0], upper_branch[1])
    lower_Bc = find_y_crossing(lower_branch[0], lower_branch[1])
    Bc = np.abs((upper_Bc - lower_Bc) / 2)

    return Bc

def loop_saturation_stats(field, magnetization, HF_cutoff=0.8, max_field_cutoff=0.97):
    '''
    ANOVA statistics for the high field portion of a hysteresis loop
    
    Parameters
    ----------
    field : numpy array
        field values
    magnetization : numpy array
        magnetization values
    HF_cutoff : float
        high field cutoff value
        default is 0.8

    Returns
    -------
    results : dict
        dictionary of the results of the ANOVA calculation
        and intermediate statistics for the ANOVA calculation

    '''
    field = np.array(field)
    magnetization = np.array(magnetization)
    upper_branch, lower_branch = split_hysteresis_loop(field, magnetization)
    # filter for the high field portion of each branch
    pos_high_field_index = np.where((field >= HF_cutoff*np.max(np.abs(field))) & (field <= max_field_cutoff*np.max(np.abs(field))))[0]
    neg_high_field_index = np.where((field <= -HF_cutoff*np.max(np.abs(field))) & (field >= -max_field_cutoff*np.max(np.abs(field))))[0]
    
    # invert points in the third quadrant to the first
    pos_high_field = field[pos_high_field_index]
    pos_high_field_magnetization = magnetization[pos_high_field_index]

    neg_high_field = field[neg_high_field_index]
    neg_high_field_magnetization = magnetization[neg_high_field_index]
    neg_high_field = -np.array(neg_high_field)
    neg_high_field_magnetization = -np.array(neg_high_field_magnetization)
    
    high_field = np.concatenate([pos_high_field, neg_high_field])
    high_field_magnetization = np.concatenate([pos_high_field_magnetization, neg_high_field_magnetization])

    anova_results = ANOVA(high_field, high_field_magnetization)
    SST = anova_results['SST']
    SSR = anova_results['SSR']
    SSD = anova_results['SSD']
    R_squared = anova_results['R_squared']

    # pure error from the mismatch between symmetrically equivalent points,
    # restricted to the same high-field window used for the lack-of-fit SSD
    # (err(H) indexed by the upper branch field covers each pair once)
    err_field = np.asarray(upper_branch[0], dtype=float)
    err = np.asarray(upper_branch[1], dtype=float) + np.asarray(lower_branch[1], dtype=float)[::-1]
    max_abs_field = np.max(np.abs(field))
    hf_pairs = (np.abs(err_field) >= HF_cutoff * max_abs_field) & \
               (np.abs(err_field) <= max_field_cutoff * max_abs_field)
    SSPE = np.sum(err[hf_pairs] ** 2) / 2
    SSLF = SSD - SSPE
    n_pairs = int(np.sum(hf_pairs))
    if n_pairs <= 2:
        raise ValueError('Too few high-field points for the lack-of-fit test; '
                         'lower HF_cutoff or measure with finer field steps')
    MSR = SSR
    MSD = SSD / (len(high_field) - 2)
    MSPE = SSPE / n_pairs
    MSLF = SSLF / (n_pairs - 2)

    FL = MSR / MSD
    FNL = MSLF / MSPE

    results = {'SST':SST,
                'SSR':SSR,
                'SSD':SSD,
                'R_squared': R_squared,
                'SSPE':SSPE,
                'SSLF':SSLF,
                'MSPE':MSPE,
                'MSR':MSR,
                'MSD':MSD,
                'FL':FL,
                'FNL':FNL}
    return results
    

def hyst_loop_saturation_test(grid_field, grid_magnetization, max_field_cutoff=0.97):
    """
    Assess the saturation state of a magnetic hysteresis loop based on linearity at high-field segments.

    This function evaluates the degree of saturation in a hysteresis loop by calculating the F statistic
    for nonlinearity (FNL, the lack-of-fit F ratio of Jackson and Solheid, 2010) over high-field windows
    starting at 60%, 70%, and 80% of the maximum field (up to a specified cutoff). A significant FNL
    (above the 2.5 threshold) indicates reproducible curvature in that window, i.e. the ferromagnetic
    moment has not saturated and a linear high-field fit is inappropriate there.

    Parameters
    ----------
    grid_field : array_like
        Array of applied magnetic field values for the hysteresis loop.
    grid_magnetization : array_like
        Array of magnetization (moment) values corresponding to `grid_field`.
    max_field_cutoff : float, optional
        Fraction of the maximum field to use as an upper cutoff for the analysis (default is 0.97).

    Returns
    -------
    results_dict : dict
        Dictionary containing:
            - 'FNL60': float, FNL for the window from 60% of the maximum field.
            - 'FNL70': float, FNL for the window from 70% of the maximum field.
            - 'FNL80': float, FNL for the window from 80% of the maximum field.
            - 'saturation_cutoff': float, lowest field fraction (0.6, 0.7, or 0.8) at which the
              high-field segment is statistically linear (saturated); 0.92 (the IRM default for
              a nonlinear fit window) if no tested window is linear.
            - 'loop_is_saturated': bool, True if the loop is saturated (linear) in at least one
              tested high-field window; False if all windows show significant nonlinearity,
              in which case an approach-to-saturation fit should be used.

    Notes
    -----
    - The function uses `loop_saturation_stats` to compute FNL values for each field fraction.
    - FNL values below 2.5 indicate statistically linear (saturated) high-field behavior;
      values above 2.5 indicate significant nonlinearity (nonsaturation).
    - The result is converted to standard Python types using `dict_in_native_python`.

    Examples
    --------
    >>> results = hyst_loop_saturation_test(fields, magnetizations)
    >>> print(results['saturation_cutoff'], results['loop_is_saturated'])
    0.8 False
    """
    
    FNL60 = loop_saturation_stats(grid_field, grid_magnetization, HF_cutoff=0.6, max_field_cutoff = max_field_cutoff)['FNL']
    FNL70 = loop_saturation_stats(grid_field, grid_magnetization, HF_cutoff=0.7, max_field_cutoff = max_field_cutoff)['FNL']
    FNL80 = loop_saturation_stats(grid_field, grid_magnetization, HF_cutoff=0.8, max_field_cutoff = max_field_cutoff)['FNL']

    saturation_cutoff = 0
    if (FNL80 > 2.5) & (FNL70 > 2.5) & (FNL60 > 2.5):
        saturation_cutoff = 0.92 # IRM default
    else:
        if FNL80 < 2.5:  #saturated at 80%
            saturation_cutoff = 0.8
        if FNL70 < 2.5:  #saturated at 70%
            saturation_cutoff = 0.7
        if FNL60 < 2.5:  #saturated at 60%
            saturation_cutoff = 0.6
    results = {'FNL60':FNL60, 'FNL70':FNL70, 'FNL80':FNL80, 'saturation_cutoff':saturation_cutoff, 'loop_is_saturated':(saturation_cutoff != 0.92)}
    results_dict = dict_in_native_python(results)
    return results_dict


def loop_closure_test(H, Mrh, Me=None, HF_cutoff=0.8, max_field_cutoff=0.99):
    '''
    function for testing whether a hysteresis loop is closed at high fields

    Mrh should be an even function of field for a well-behaved loop
    (Mrh(-H) = Mrh(H)), so its field-reflection average (even part, with
    unphysical negative values set to zero) is taken as the signal. A loop
    that remains open at high fields (e.g. due to unsaturated high-coercivity
    phases such as hematite or goethite) retains a significant Mrh signal in
    the high-field window, giving a high signal-to-noise ratio (SNR) and a
    high ratio of high-field Mrh area to total Mrh area (HAR). The noise is
    estimated from the high-field portion of the err(H) curve when `Me` is
    provided (matching the HystLab implementation of this test; Paterson et
    al., 2018, section 4.5), or from the odd part of Mrh otherwise. Fields
    above max_field_cutoff (default 99%) of the maximum field are excluded
    from the high-field windows to avoid extreme-tip artifacts.

    Parameters
    ----------
    H: array-like
        field values of the upper branch (ascending)
    Mrh: array-like
        remanent hysteretic magnetization Mrh(H)
    Me: array-like, optional
        error curve err(H) on the same field axis (as returned by
        calc_Mr_Mrh_Mih_Brh); used as the noise estimate when provided
    HF_cutoff: float
        high field cutoff value taken as fraction of the max field value
    max_field_cutoff: float
        upper trim of the high-field windows as fraction of the max field

    Returns
    -------
    results : dict
        Dictionary containing:
            - 'SNR': float, high-field signal-to-noise ratio in dB
            - 'HAR': float, high-field to total Mrh area ratio in dB
            - 'loop_is_closed': bool, True if SNR < 8 dB or HAR < -48 dB
    '''
    assert len(H) == len(Mrh), 'H, Mrh must have the same length'
    H = np.asarray(H, dtype=float)
    Mrh = np.asarray(Mrh, dtype=float)
    max_H = np.max(np.abs(H))

    pos_H_index = np.where(H > 0)
    neg_H_index = np.where(H < 0)
    pos_H = H[pos_H_index]
    pos_Mrh = Mrh[pos_H_index]
    neg_Mrh = Mrh[neg_H_index]

    pos_HF_index = np.where((H > HF_cutoff*max_H) & (H <= max_field_cutoff*max_H))
    neg_HF_index = np.where((H < -HF_cutoff*max_H) & (H >= -max_field_cutoff*max_H))
    pos_HF = H[pos_HF_index]
    pos_HF_Mrh = Mrh[pos_HF_index]
    neg_HF_Mrh = Mrh[neg_HF_index]

    # field-reflection average of Mrh (signal); negative values are noise
    # excursions and are set to 0 so that only positive signal is counted
    average_Mrh = (pos_Mrh + neg_Mrh[::-1])/2
    average_Mrh[average_Mrh < 0] = 0
    average_HF_Mrh = (pos_HF_Mrh + neg_HF_Mrh[::-1])/2
    average_HF_Mrh[average_HF_Mrh < 0] = 0

    if Me is not None:
        # noise from the high-field portion of the err(H) curve, over both
        # field polarities (the HystLab convention)
        Me = np.asarray(Me, dtype=float)
        assert len(Me) == len(H), 'H, Me must have the same length'
        hf_noise = Me[(np.abs(H) > HF_cutoff*max_H) & (np.abs(H) <= max_field_cutoff*max_H)]
    else:
        # fall back to the odd part of Mrh (the residual between the field
        # polarities); for white noise this runs ~3 dB below the err(H)-based
        # estimate, biasing slightly toward classifying loops as open
        hf_noise = pos_HF_Mrh - neg_HF_Mrh[::-1]

    HF_Mrh_signal_RMS = np.sqrt(np.mean(average_HF_Mrh**2))
    HF_Mrh_noise_RMS = np.sqrt(np.mean(hf_noise**2))
    SNR = 20*np.log10(HF_Mrh_signal_RMS/HF_Mrh_noise_RMS)

    total_Mrh_area = np.trapezoid(average_Mrh, pos_H)
    HF_Mrh_area = np.trapezoid(average_HF_Mrh, pos_HF)

    HAR = 20*np.log10(HF_Mrh_area/total_Mrh_area)
    loop_is_closed = (SNR < 8) or (HAR < -48)

    results = {'SNR':float(SNR),
               'HAR':float(HAR),
               'loop_is_closed':bool(loop_is_closed),
               }
    return results


def drift_correction_Me(H, M):
    """
    Perform default IRM drift correction for a hysteresis loop based on the Me method.

    This function applies a drift correction algorithm to magnetization data (M) measured as a function of applied field (H),
    commonly used for IRM (Isothermal Remanent Magnetization) experiments. The correction is based on the Me signal,
    which is the sum of the upper and reversed lower branches of the hysteresis loop.
    The correction method adapts depending on whether significant drift is detected in the high-field region.

    Parameters
    ----------
    H : numpy.ndarray
        Array of magnetic field values.
    M : numpy.ndarray
        Array of measured magnetization values corresponding to `H`.

    Returns
    -------
    M_cor : numpy.ndarray
        Corrected magnetization values after drift correction.

    Examples
    --------
    >>> H = np.linspace(-1, 1, 200)
    >>> M = measure_hysteresis(H)
    >>> M_cor = drift_correction_Me(H, M)
    >>> plot(H, M, label='Original')
    >>> plot(H, M_cor, label='Drift Corrected')
    """
    # split loop branches
    upper_branch, lower_branch = split_hysteresis_loop(H, M)
    # calculate Me
    Me = upper_branch[1][::-1] + lower_branch[1]

    loop_size = len(H) -1 
    half_loop_size = loop_size // 2
    quarter_loop_size = loop_size // 4
    # calculate the smoothed Me using Savitzky-Golay filter
    # which allows inplementation of a polynomial fit to the data within each window
    smoothed_Me = savgol_filter(Me, window_length=11, polyorder=2, mode='interp')
    # determine whether the main drift field region
    main_drift_region = H[np.argmax(np.abs(smoothed_Me[:half_loop_size]))]

    M_cor = copy.deepcopy(M)
    positive_field_cor = abs(main_drift_region) > np.max(H) * 0.75

    if positive_field_cor:
        # if the ratio of drift in the high-field range (≥75% of the peak field) to the low-field range.
        # is high, then the positive field correction is applied
        for i in range(0, quarter_loop_size):
            M_cor[i] -= smoothed_Me[i]
            M_cor[loop_size - i] -= smoothed_Me[half_loop_size - i]

        return M_cor
    else: 
        # if positive field correctionis not preferred, we do upper branch drift correction
        window_size = 7
        # calculate running mean of the upper branch with a window size of 2k+1
        kernel = np.ones(window_size) / window_size
        Me_running_mean = np.convolve(Me, kernel, mode='same')
        
        for i in range(len(Me_running_mean)):
            
            M_cor[i] = M[i] - Me_running_mean[i]
        return M_cor
    
def prorated_drift_correction(field, magnetization):
    '''
    function to correct for the linear drift of a hysteresis loop
        take the difference between the magnetization measured at the maximum field on the upper and lower branches
        apply linearly prorated correction of M(H)
        this should be applied to the gridded data

    Note: the prorated ramp assumes the array order corresponds to measurement
    time with the upper (descending) branch first, which is the order produced
    by `grid_hysteresis_loop`. For loops originally measured in the opposite
    sweep order the correction still closes the loop but attributes the drift
    with the opposite sense.

    Parameters
    ----------
    field : numpy array
        field values
    magnetization : numpy array
        magnetization values

    Returns
    -------
    corrected_magnetization : numpy array
        corrected magnetization values
    '''

    field = np.array(field)
    magnetization = np.array(magnetization)
    upper_branch, lower_branch = split_hysteresis_loop(field, magnetization)

    # find the maximum field values for the upper and lower branches
    upper_branch_max_idx = np.argmax(upper_branch[0])
    lower_branch_max_idx = np.argmax(lower_branch[0])

    # find the difference between the magnetization values at the maximum field values
    M_ce = upper_branch[1][upper_branch_max_idx] - lower_branch[1][lower_branch_max_idx]

    # apply linearly prorated correction of M(H)
    # delta_M_i = M_ce * (i/(N-1) - 1/2) with 0-based i, which averages to zero
    # over the loop and removes the closure error M_ce between first and last points
    corrected_magnetization = [M_ce * (i/(len(field)-1) - 1/2) + magnetization[i] for i in range(len(field))]

    return np.array(corrected_magnetization)

def symmetric_averaging_drift_corr(field, magnetization):
    """
    Apply symmetric averaging drift correction to a hysteresis loop.

    This function corrects drift in magnetic hysteresis loop data by averaging the upper branch and
    the inverted lower branch of the magnetization curve, then adjusting for tip-to-tip separation.
    The corrected magnetization is constructed by concatenating the reversed, drift-corrected upper branch
    and its inverted counterpart, restoring symmetry to the loop.

    Parameters
    ----------
    field : array_like
        Array of applied magnetic field values for the hysteresis loop.
    magnetization : array_like
        Array of measured magnetization values corresponding to `field`.

    Returns
    -------
    corrected_magnetization : numpy.ndarray
        Array of drift-corrected magnetization values, symmetrically constructed for the full loop.

    Examples
    --------
    >>> field = np.linspace(-1, 1, 200)
    >>> magnetization = some_hysteresis_measurement(field)
    >>> corrected = symmetric_averaging_drift_corr(field, magnetization)
    """
    field = np.array(field)
    magnetization = np.array(magnetization)

    upper_branch, lower_branch = split_hysteresis_loop(field, magnetization)

    # average the upper and inverted lower branches
    averaged_upper_branch = (upper_branch[1] - lower_branch[1][::-1]) / 2

    # calculate tip-to-tip separation from both the upper and lower branches
    tip_to_tip_separation = (upper_branch[1][0] - lower_branch[1][0] + upper_branch[1][-1] - lower_branch[1][-1]) / 4
    # apply the tip-to-tip separation to the upper branch
    corrected_magnetization = averaged_upper_branch - tip_to_tip_separation

    # append back in the lower branch which should just be the inverted corrected upper branch
    corrected_magnetization = np.concatenate([corrected_magnetization[::-1], -corrected_magnetization[::-1]])

    return corrected_magnetization

def IRM_nonlinear_fit(H, chi_HF, Ms, a_1, a_2):
    """
    Calculate the non-linear fit for Isothermal Remanent Magnetization (IRM) as a function of applied field.

    This function models the IRM signal as a sum of high-field linear susceptibility, 
    saturation magnetization, and non-linear correction terms with inverse field dependence.
    The model is commonly used for fitting high-field IRM data, especially for extracting 
    parameters such as high-field susceptibility (chi_HF) and saturation magnetization (Ms).

    Parameters
    ----------
    H : numpy.ndarray
        Array of applied magnetic field values (in Tesla).
    chi_HF : float
        High-field magnetic susceptibility.Cconverted to Tesla to match the unit of the field.
    Ms : float
        Saturation magnetization (in the same units as IRM).
    a_1 : float
        Coefficient for the H^(-1) non-linear correction term. Should be negative.
    a_2 : float
        Coefficient for the H^(-2) non-linear correction term. Should be negative.

    Returns
    -------
    IRM_fit : numpy.ndarray
        Array of fitted IRM values corresponding to each field value in `H`.

    Examples
    --------
    >>> H = np.linspace(0.1, 3, 100)  # field in Tesla, avoid zero for stability
    >>> fit = IRM_nonlinear_fit(H, chi_HF=0.02, Ms=1.2, a_1=-0.03, a_2=-0.01)
    >>> import matplotlib.pyplot as plt
    >>> plt.plot(H, fit)
    >>> plt.xlabel('Field (T)')
    >>> plt.ylabel('IRM fit')
    >>> plt.show()
    """
    
    chi_HF = chi_HF/(4*np.pi/1e7)
    return chi_HF * H + Ms + a_1 * H**(-1) + a_2 * H**(-2)

def IRM_nonlinear_fit_cost_function(params, H, M_obs):
    '''
    Cost function for the IRM non-linear least squares fit optimization

    Parameters
    ----------
    params : numpy array
        array of parameters to optimize
    H : numpy array
        field values
    M_obs : numpy array
        observed magnetization values

    Returns
    -------
    residual : numpy array
        residual between the observed and predicted magnetization values
    '''

    chi_HF, Ms, a_1, a_2 = params
    prediction = IRM_nonlinear_fit(H, chi_HF, Ms, a_1, a_2)
    return M_obs - prediction

def Fabian_nonlinear_fit(H, chi_HF, Ms, alpha, beta):
    '''
    function for calculating the Fabian non-linear fit

    Parameters
    ----------
    H : numpy array
        field values
    chi_HF : float
        high field susceptibility
    Ms : float
        saturation magnetization
    alpha : float
        coefficient for H^(beta), needs to be negative
    beta : float
        coefficient for H^(beta), needs to be negative

    Returns
    -----------

    numpy array of the same shape as H, giving the fitted magnetization values for each field value provided

    '''
    chi_HF = chi_HF/(4*np.pi/1e7) # convert to Tesla
    return chi_HF * H + Ms + alpha * H**beta

def Fabian_nonlinear_fit_cost_function(params, H, M_obs):
    '''
    cost function for the Fabian non-linear least squares fit optimization

    Parameters
    ----------
    params : numpy array
        array of parameters to optimize
    H : numpy array
        field values
    M_obs : numpy array
        observed magnetization values

    Returns
    -------
    residual : numpy array
        residual between the observed and predicted magnetization values
    '''

    chi_HF, Ms, alpha, beta = params
    prediction = Fabian_nonlinear_fit(H, chi_HF, Ms, alpha, beta)
    return M_obs - prediction

def Fabian_nonlinear_fit_fix_beta_cost_function(params, H, M_obs):
    '''
    cost function for the Fabian non-linear least squares fit optimization
        with beta fixed at -2

    Parameters
    ----------
    params : numpy array
        array of parameters to optimize
    H : numpy array
        field values
    M_obs : numpy array
        observed magnetization values

    Returns
    -------
    residual : numpy array
        residual between the observed and predicted magnetization values
    '''
    beta = -2 
    chi_HF, Ms, alpha = params
    prediction = Fabian_nonlinear_fit(H, chi_HF, Ms, alpha, beta)
    return M_obs - prediction

def hyst_HF_nonlinear_optimization(H, M, HF_cutoff, fit_type, initial_guess=[1, 1, -0.1, -0.1], bounds=([0, 0, -np.inf, -np.inf], [np.inf, np.inf, 0, 0])):
    '''
    Optimize a high-field nonlinear fit

    Parameters
    ----------
    H : numpy.ndarray
        Array of field values.
    M : numpy.ndarray
        Array of magnetization values.
    HF_cutoff : float
        Fraction of max(|H|) defining the lower bound of the high-field region.
    fit_type : {'IRM', 'Fabian', 'Fabian_fixed_beta'}
        Type of nonlinear model to fit.
    initial_guess : list of float, optional
        Initial parameter guess for the optimizer.
        Defaults to [1, 1, -0.1, -0.1]:
        χ_HF = 1, Mₛ = 1, a₁ = –0.1, a₂ = –0.1 (or α, β for Fabian).
    bounds : tuple of array-like, optional
        Lower and upper bounds for each parameter.
        Defaults to ([0, 0, -∞, -∞], [∞, ∞, 0, 0]):
        - Lower: χ_HF ≥ 0, Mₛ ≥ 0, a₁ ≥ –∞, a₂ ≥ –∞  
        - Upper: χ_HF ≤ ∞, Mₛ ≤ ∞, a₁ ≤ 0, a₂ ≤ 0  
        (for Fabian, α and β follow the same positions/limits).
    
    Returns
    -------
    dict
        Fit results with keys:
        - 'chi_HF', 'Ms', 'a_1', 'a_2' (for IRM) or
          'chi_HF', 'Ms', 'alpha', 'beta' (for Fabian variants)
        - 'Fnl_lin': float, F statistic for the improvement of the nonlinear fit
          over a linear fit (Jackson and Solheid, 2010, equation 21); values above
          ~3-3.5 indicate a statistically significant improvement for the
          4-parameter models (for 'Fabian_fixed_beta' the degrees of freedom are
          (1, N-3) and the 5% critical value is ~3.9-4.0). Because the nonlinear
          coefficients are constrained non-positive, the statistic is conservative
          under the null (saturated loops give values well below the critical
          value, occasionally marginally negative when the bounded fit is a hair
          worse than unconstrained least squares).
    '''
    HF_index = np.where((np.abs(H) >= HF_cutoff*np.max(np.abs(H))) & (np.abs(H) <= 0.97*np.max(np.abs(H))))[0]

    HF_field = np.abs(H[HF_index])
    HF_magnetization = np.where(H[HF_index] >= 0, M[HF_index], -M[HF_index])

    if fit_type == 'IRM':
        cost_function = IRM_nonlinear_fit_cost_function
        results = least_squares(cost_function, initial_guess, bounds=bounds, args=(HF_field, HF_magnetization))
    elif fit_type == 'Fabian':
        cost_function = Fabian_nonlinear_fit_cost_function
        results = least_squares(cost_function, initial_guess, bounds=bounds, args=(HF_field, HF_magnetization))
    elif fit_type == 'Fabian_fixed_beta':
        cost_function = Fabian_nonlinear_fit_fix_beta_cost_function
        results = least_squares(cost_function, initial_guess[:3], bounds=(bounds[0][:3], bounds[1][:3]), args=(HF_field, HF_magnetization))
    else:
        raise ValueError('Fit type must be either IRM or Fabian')

    if fit_type == 'IRM':
        final_result = {'chi_HF': results.x[0], 'Ms': results.x[1], 'a_1': results.x[2], 'a_2': results.x[3]}
        chi_HF, Ms, a_1, a_2 = results.x
        nonlinear_fit = IRM_nonlinear_fit(HF_field, chi_HF, Ms, a_1, a_2)
    elif fit_type == 'Fabian':
        final_result = {'chi_HF': results.x[0], 'Ms': results.x[1], 'alpha': results.x[2], 'beta': results.x[3]}
        chi_HF, Ms, alpha, beta = results.x
        nonlinear_fit = Fabian_nonlinear_fit(HF_field, chi_HF, Ms, alpha, beta)
    elif fit_type == 'Fabian_fixed_beta':
        final_result = {'chi_HF': results.x[0], 'Ms': results.x[1], 'alpha': results.x[2], 'beta': -2}
        chi_HF, Ms, alpha = results.x
        nonlinear_fit = Fabian_nonlinear_fit(HF_field, chi_HF, Ms, alpha, -2)

    # Fnl_lin (Jackson and Solheid, 2010, equation 21) tests whether the nonlinear fit
    # significantly improves on a linear fit:
    # Fnl_lin = [(SSD_lin - SSD_nl)/(p_nl - p_lin)] / [SSD_nl/(N - p_nl)]
    # where p are the number of model parameters. Values above ~3-3.5 indicate a
    # statistically significant improvement from the nonlinear term(s).
    linear_fit_ANOVA = ANOVA(HF_field, HF_magnetization)
    SSD_lin = linear_fit_ANOVA['SSD']
    SSD_nl = np.sum((HF_magnetization - nonlinear_fit) ** 2)

    n_points = len(HF_magnetization)
    p_lin = 2
    p_nl = 3 if fit_type == 'Fabian_fixed_beta' else 4
    Fnl_lin = ((SSD_lin - SSD_nl) / (p_nl - p_lin)) / (SSD_nl / (n_points - p_nl))

    final_result['Fnl_lin'] = Fnl_lin
    final_result_dict = dict_in_native_python(final_result)
    return final_result_dict


def process_hyst_loop(field, magnetization, specimen_name='', show_results_table=True, show_plot=True,
                      NL_fit=False, centering_protocol='legacy'):
    """
    Process a magnetic hysteresis loop using the IRM decision tree workflow.

    This function performs a complete analysis of a hysteresis loop, including gridding, centering, drift correction,
    high-field correction, and extraction of key magnetic parameters. The workflow follows best practices in rock magnetism
    and outputs both a summary of results and a Bokeh plot visualizing the various processing steps.

    The inputs need not come from a MagIC measurements table: any pair of
    field and magnetization sequences (lists, arrays, or dataframe columns)
    can be processed. Inputs are passed through `sanitize_hysteresis_inputs`,
    so non-finite measurement pairs are dropped with a report, numeric
    strings are converted, and either field sweep order (starting from
    positive or negative saturation) is accepted.

    Parameters
    ----------
    field : array_like
        Array of applied magnetic field values in tesla (the chi_HF unit
        conversions assume tesla; a warning is printed if the values appear
        to be in mT or Oe).
    magnetization : array_like
        Array of magnetization values (same length as `field`), in any
        consistent unit; mass-normalized Am2/kg matches MagIC conventions.
    specimen_name : str, optional
        Identifier for the specimen, used for labeling plots.
    show_results_table : bool, optional
        If True (default), display a summary table of key parameters using Bokeh.
    show_plot : bool, optional
        If True (default), display the Bokeh plot of the hysteresis loop and processing steps.
    NL_fit : bool, optional
        If True, force non-linear high-field fitting regardless of the saturation test result (default is False).
    centering_protocol : {'legacy', 'iterative'}, optional
        Centering workflow to apply before drift and high-field corrections.
        Defaults to 'legacy' for backward compatibility.

    Returns
    -------
    results : dict
        Dictionary containing the following keys:
            - 'gridded_H': gridded field values
            - 'gridded_M': gridded magnetization values
            - 'linearity_test_results': results of the initial linearity test
            - 'loop_is_linear': whether the loop passes the linearity test
            - 'FNL': F statistic for whole-loop nonlinearity (lack-of-fit F ratio)
            - 'loop_centering_results': results of centering optimization
            - 'centered_H': centered field values
            - 'centered_M': centered magnetization values
            - 'drift_corrected_M': drift-corrected magnetization
            - 'slope_corrected_M': slope-corrected magnetization
            - 'loop_closure_test_results': results of closure test
            - 'loop_is_closed': whether the loop is closed
            - 'loop_saturation_stats': saturation test results
            - 'loop_is_saturated': whether the loop is saturated
            - 'M_sn', 'Q': quality metrics from centering
            - 'H', 'Mr', 'Mrh', 'Mih', 'Me', 'Brh': characteristic field and moment parameters
            - 'sigma': shape parameter (Fabian, 2003)
            - 'chi_HF': high-field susceptibility
            - 'FNL60', 'FNL70', 'FNL80': high-field nonlinearity F statistics for windows
              starting at 60%, 70%, and 80% of the maximum field
            - 'Ms': saturation magnetization
            - 'Bc': coercive field
            - 'M_sn_f', 'Qf': quality metrics for ferromagnetic component
            - 'Fnl_lin': F statistic for improvement of the nonlinear over the linear
              high-field fit (None if the loop is saturated and no nonlinear fit is made)
            - 'plot': Bokeh figure with overlaid processing steps
    """
    # clean the inputs (accepts lists/Series/text columns, drops non-finite
    # pairs, warns on apparent non-tesla field units)
    field, magnetization = sanitize_hysteresis_inputs(field, magnetization)

    # first grid the data into symmetric field values
    grid_fields, grid_magnetizations = grid_hysteresis_loop(field, magnetization)

    # test linearity of the gridded original loop
    loop_linearity_test_results = hyst_linearity_test(grid_fields, grid_magnetizations)

    # loop centering
    if centering_protocol == 'legacy':
        loop_centering_results = hyst_loop_centering(grid_fields, grid_magnetizations)
    elif centering_protocol == 'iterative':
        loop_centering_results = hyst_loop_centering_iterative(grid_fields, grid_magnetizations)
    else:
        raise ValueError("centering_protocol must be either 'legacy' or 'iterative'")

    # check if the quality factor Q is < 2
    if loop_centering_results['Q'] < 2:
        # in case the loop quality is bad, no field correction is applied
        loop_centering_results['opt_H_offset'] = 0
        loop_centering_results['centered_H'] = grid_fields
        loop_centering_results['centered_M'] = grid_magnetizations - loop_centering_results['opt_M_offset']

    centered_H, centered_M = loop_centering_results['centered_H'], loop_centering_results['centered_M']

    # drift correction
    drift_corr_M = drift_correction_Me(centered_H, centered_M)

    # calculate Mr, Mrh, Mih, Me, Brh
    H, Mr, Mrh, Mih, Me, Brh = calc_Mr_Mrh_Mih_Brh(centered_H, drift_corr_M)

    # check if the loop is closed
    loop_closure_test_results = loop_closure_test(H, Mrh, Me)

    # check if the loop is saturated (high field linearity test)
    loop_saturation_stats = hyst_loop_saturation_test(centered_H, drift_corr_M)
    if NL_fit:
        loop_saturation_stats['loop_is_saturated'] = False  # force non-linear high-field fitting

    if loop_saturation_stats['loop_is_saturated']:
        # linear high field correction
        chi_HF, Ms = linear_HF_fit(centered_H, drift_corr_M, loop_saturation_stats['saturation_cutoff'])
        Fnl_lin = None
    else:
        # do non linear approach to saturation fit
        NL_fit_result = hyst_HF_nonlinear_optimization(centered_H, drift_corr_M, 0.6, 'IRM')
        chi_HF, Ms, Fnl_lin = NL_fit_result['chi_HF'], NL_fit_result['Ms'], NL_fit_result['Fnl_lin']

     # apply high field correction
    slope_corr_M = hyst_slope_correction(centered_H, drift_corr_M, chi_HF)

    # calculate the Msn and Q factor for the ferromagentic component
    M_sn_f, Qf = calc_Q(centered_H, slope_corr_M)

    # calculate the coercivity Bc
    Bc = calc_Bc(centered_H, slope_corr_M)

    # calculate the shape parameter of Fabian 2003
    E_hyst = np.trapezoid(Mrh, H)
    sigma = np.log(E_hyst / 2 / Bc / Ms)

    p = None
    p_slope_corr = None
    if _HAS_BOKEH:
        # plot original loop
        p = plot_hysteresis_loop(grid_fields, grid_magnetizations, specimen_name, line_color='orange', label='raw loop', 
                                 return_figure=True, show_plot=False)
        # plot centered loop
        p_centered = plot_hysteresis_loop(centered_H, centered_M, specimen_name, p=p, line_color='red', label=specimen_name+' offset corrected', 
                                          return_figure=True, show_plot=False)
        # plot drift corrected loop
        p_drift_corr = plot_hysteresis_loop(centered_H, drift_corr_M, specimen_name, p=p_centered, line_color='pink', label=specimen_name+' drift corrected', 
                                            return_figure=True, show_plot=False)
        # plot slope corrected loop
        p_slope_corr = plot_hysteresis_loop(centered_H, slope_corr_M, specimen_name, p=p_drift_corr, line_color='blue', label=specimen_name+' slope corrected', 
                                            return_figure=True, show_plot=False)
        # plot Mrh
        p_slope_corr.line(H, Mrh, line_color='green', legend_label='Mrh', line_width=1)
        p_slope_corr.line(H, Mih, line_color='purple', legend_label='Mih', line_width=1)
        p_slope_corr.line(H, Me, line_color='brown', legend_label='Me', line_width=1)
        if show_plot:
            show(p_slope_corr)
    results = {'gridded_H': grid_fields, 
               'gridded_M': grid_magnetizations, 
               'linearity_test_results': loop_linearity_test_results,
               'loop_is_linear': loop_linearity_test_results['loop_is_linear'],
               'FNL': loop_linearity_test_results['FNL'],
               'loop_centering_results': loop_centering_results,
               'centering_protocol': centering_protocol,
               'centered_H': centered_H, 
               'centered_M': centered_M, 
               'drift_corrected_M': drift_corr_M,
               'slope_corrected_M': slope_corr_M,
               'loop_closure_test_results': loop_closure_test_results,
                'loop_is_closed': loop_closure_test_results['loop_is_closed'],
               'loop_saturation_stats': loop_saturation_stats,
                'loop_is_saturated': loop_saturation_stats['loop_is_saturated'],
               'M_sn':loop_centering_results['M_sn'],
               'Q': loop_centering_results['Q'],
               'H': H, 'Mr': Mr, 'Mrh': Mrh, 
               'Mih': Mih, 'Me': Me, 'Brh': Brh, 'sigma': sigma,
               'chi_HF': chi_HF, 
               'FNL60': loop_saturation_stats['FNL60'],
               'FNL70': loop_saturation_stats['FNL70'],
               'FNL80': loop_saturation_stats['FNL80'],
               'Ms': Ms, 'Bc': Bc, 'M_sn_f': M_sn_f,
               'Qf': Qf, 'Fnl_lin': Fnl_lin,
               'plot': p}
    
    if show_results_table and _HAS_BOKEH and p_slope_corr is not None:
        summary = {
            'Mr':    [Mr],
            'Ms':    [Ms],
            'Bc':    [Bc],
            'Brh':   [Brh],
            'sigma': [sigma],
            'Q':     [loop_centering_results['Q']],
            'Qf':    [Qf],
            'chi_HF':[chi_HF],
            'FNL60': [loop_saturation_stats['FNL60']],
            'FNL70': [loop_saturation_stats['FNL70']],
            'FNL80': [loop_saturation_stats['FNL80']],
        }
        src = ColumnDataSource(summary)
        cols = [
            TableColumn(field=param, title=param)
            for param in summary
        ]
        data_table = DataTable(
            source=src, columns=cols,
            width=p_slope_corr.width, height=100
        )
        data_table.index_position = None 
        layout = column(data_table)
        show(layout)
    return results

def process_hyst_loops(
    hyst_experiments,
    measurements,
    field_col="meas_field_dc",
    magn_col="magn_mass",
    show_results_table=True,
    show_plots=True,
    centering_protocol='legacy',
):
    """
    Process multiple hysteresis loops in batch.

    Parameters
    ----------
    hyst_experiments : DataFrame
        Must contain columns "experiment" and "specimen".
    measurements : DataFrame
        Must contain an "experiment" column and the data columns.
    field_col : str, optional
        Name of the column in `measurements` holding field values.
        Defaults to "meas_field_dc".
    magn_col : str, optional
        Name of the column in `measurements` holding magnetization values.
        Defaults to "magn_mass".
    show_results_table : bool, optional
        If True, display the summary table below each plot.
    show_plots : bool, optional
        If True, display the hysteresis plots for each specimen.
    centering_protocol : {'legacy', 'iterative'}, optional
        Centering workflow to pass through to process_hyst_loop.
        Defaults to 'legacy' for backward compatibility.

    Returns
    -------
    results_df : pandas.DataFrame
        DataFrame with hysteresis results for each experiment.
        Has a numeric index with 'specimen' and 'experiment' as columns.
    """
    results = []
    for _, row in hyst_experiments.iterrows():
        exp = row["experiment"]
        spec = row["specimen"]
        df = (
            measurements[measurements["experiment"] == exp]
            .reset_index(drop=True)
        )
        res = process_hyst_loop(
            df[field_col].values,
            df[magn_col].values,
            spec,
            show_results_table=show_results_table,
            show_plot=show_plots,
            centering_protocol=centering_protocol,
        )
        res['specimen'] = spec
        res['experiment'] = exp
        res['processed_by'] = pmagpy_version
        results.append(res)
    results_df = pd.DataFrame(results)
    return results_df


def add_hyst_stats_to_specimens_table(specimens_df, hyst_results, overwrite=True):
    '''
    Return a copy of the specimens table with hysteresis results added.

    The input DataFrame is not modified. Assign the return value to
    update your table, e.g.:
        specimens = add_hyst_stats_to_specimens_table(specimens, hyst_results)

    Parameters
    ----------
    specimens_df : pandas.DataFrame
        dataframe with the specimens data
    hyst_results : pandas.DataFrame
        DataFrame with hysteresis results including 'specimen' and
        'experiment' columns, as output from rmag.process_hyst_loops.
        Has a numeric index (one row per experiment).
    overwrite : bool, optional
        If True (default), existing MagIC column values and description stats
        are replaced with new values from hyst_results. If False, existing
        rows are preserved as-is and new rows are appended with the
        hyst results.

    Returns
    -------
    specimens_df : pandas.DataFrame
        A new DataFrame with hysteresis results added.
        If a specimen has multiple experiments, its row is duplicated
        so that each experiment gets its own row.
    '''

    specimens_df = specimens_df.copy()

    result_keys_MagIC = ['Ms', 'Mr', 'Bc', 'chi_HF']
    MagIC_columns = ['hyst_ms_mass', 'hyst_mr_mass', 'hyst_bc', 'hyst_xhf']

    additional_keys = ['Q', 'Qf', 'sigma',
                'Brh', 'FNL', 'FNL60', 'FNL70', 'FNL80',
                'Fnl_lin', 'loop_is_linear', 'loop_is_closed', 'loop_is_saturated',
                'processed_by']

    # ensure MagIC columns exist in specimens_df
    for col in MagIC_columns:
        if col not in specimens_df.columns:
            specimens_df[col] = np.nan
    if 'description' not in specimens_df.columns:
        specimens_df['description'] = np.nan

    # Coerce target columns so scalar writes succeed across pandas versions.
    # MagIC tables are read as text, so these arrive as string dtype under
    # pandas >= 3.0 (future.infer_string), which rejects assigning a float
    # (numeric stats) or a description string into a string-dtype column.
    for col in MagIC_columns:
        specimens_df[col] = pd.to_numeric(specimens_df[col], errors='coerce')
    specimens_df['description'] = specimens_df['description'].astype(object)

    for _, row in hyst_results.iterrows():
        specimen_name = row['specimen']
        experiment_name = row['experiment']
        mask = specimens_df['experiments'] == experiment_name

        if overwrite:
            if not mask.any():
                # no row for this experiment — create one from specimen template
                spec_mask = specimens_df['specimen'] == specimen_name
                if spec_mask.any():
                    new_row = specimens_df.loc[spec_mask].iloc[0].copy()
                else:
                    new_row = pd.Series(dtype='object')
                    new_row['specimen'] = specimen_name
                new_row['experiments'] = experiment_name
                specimens_df = pd.concat(
                    [specimens_df, new_row.to_frame().T],
                    ignore_index=True,
                )
                mask = specimens_df['experiments'] == experiment_name
            ipos = mask.values.nonzero()[0][0]
        else:
            # overwrite=False: leave existing row alone, always add a new row
            spec_mask = specimens_df['specimen'] == specimen_name
            if spec_mask.any():
                new_row = specimens_df.loc[spec_mask].iloc[0].copy()
            else:
                new_row = pd.Series(dtype='object')
                new_row['specimen'] = specimen_name
            new_row['experiments'] = experiment_name
            specimens_df = pd.concat(
                [specimens_df, new_row.to_frame().T],
                ignore_index=True,
            )
            ipos = len(specimens_df) - 1

        # write MagIC columns
        for result_key, col in zip(result_keys_MagIC, MagIC_columns):
            specimens_df.iloc[ipos, specimens_df.columns.get_loc(col)] = row[result_key]

        # build and write additional stats into description
        additional_stats_dict = {key: row[key] for key in additional_keys
                                 if key in row.index}
        desc_col = specimens_df.columns.get_loc('description')
        desc = specimens_df.iloc[ipos, desc_col]
        if isinstance(desc, str):
            try:
                description_dict = eval(desc)
                if isinstance(description_dict, dict):
                    description_dict.update(additional_stats_dict)
                    specimens_df.iloc[ipos, desc_col] = str(description_dict)
                else:
                    raise ValueError
            except (SyntaxError, ValueError, NameError):
                additional_stats_dict['description'] = desc
                specimens_df.iloc[ipos, desc_col] = str(additional_stats_dict)
        else:
            specimens_df.iloc[ipos, desc_col] = str(additional_stats_dict)

    return specimens_df

# X-T functions
# ------------------------------------------------------------------------------------------------------------------

def split_warm_cool(experiment,temperature_column='meas_temp',
                    magnetic_column='susc_chi_mass'):
    """
    Split a thermomagnetic curve into heating and cooling portions. Default
    columns are 'meas_temp' and 'susc_chi_mass' for susceptibility measurements.
    Funcation can also be used for other warming then cooling data.

    Parameters
    ----------
    experiment : pandas.DataFrame
        the experiment data
    temperature_column : str, optional
        name of the temperature column (default 'meas_temp')
    magnetic_column : str, optional
        name of the magnetization/susceptibility column
        (default 'susc_chi_mass')

    Returns
    -------
    warm_T : list[float]
        temperatures for the heating cycle
    warm_X : list[float]
        magnetization/susceptibility for the heating cycle
    cool_T : list[float]
        temperatures for the cooling cycle
    cool_X : list[float]
        magnetization/susceptibility for the cooling cycle
    """
    Tlist = experiment[temperature_column] # temperature list
    Xlist = experiment[magnetic_column] # Chi list
    
    warmorcool = np.array(np.insert((np.diff(Tlist) > 0 )* 1, 0, 1))
#     print(warmorcool)
    warm_T = [Tlist[i] for i in range(len(warmorcool)) if warmorcool[i]==1]
    cool_T = [Tlist[i] for i in range(len(warmorcool)) if warmorcool[i]==0]
    warm_X = [Xlist[i] for i in range(len(warmorcool)) if warmorcool[i]==1]
    cool_X = [Xlist[i] for i in range(len(warmorcool)) if warmorcool[i]==0]

    return warm_T, warm_X, cool_T, cool_X


def plot_X_T(
    experiment,
    temperature_column="meas_temp",
    magnetic_column="susc_chi_mass",
    temp_unit="C",
    smooth_window=0,
    remove_holder=True,
    plot_derivative=True,
    plot_inverse=False,
    interactive=True,
    return_figure=False,
    figsize=(6, 6),
):
    """
    Plot the high-temperature susceptibility curve, and optionally its derivative
    and reciprocal using Bokeh or Matplotlib.

    Parameters:
        experiment (pandas.DataFrame): MagIC-formatted experiment DataFrame.
        temperature_column (str): Name of temperature column.
        magnetic_column (str): Name of susceptibility column.
        temp_unit (str): "C" for Celsius.
        smooth_window (int): Window for smoothing, if 0, no smoothing is applied.
        remove_holder (bool): Subtract holder signal.
        plot_derivative (bool): Plot derivative.
        plot_inverse (bool): Plot inverse.
        interactive (bool): True for Bokeh, False for Matplotlib.
        return_figure (bool): Return figure objects if True.
        figsize (tuple): (width, height) in inches.
    """
    warm_T, warm_X, cool_T, cool_X = split_warm_cool(
        experiment,
        temperature_column=temperature_column,
        magnetic_column=magnetic_column,
    )
    if temp_unit == "C":
        warm_T = [T - 273.15 for T in warm_T]
        cool_T = [T - 273.15 for T in cool_T]
    else:
        raise ValueError('temp_unit must be "C"')
    if remove_holder:
        holder_w = min(warm_X)
        holder_c = min(cool_X)
        warm_X = [X - holder_w for X in warm_X]
        cool_X = [X - holder_c for X in cool_X]
    swT, swX = smooth_moving_avg(warm_T, warm_X, smooth_window)
    scT, scX = smooth_moving_avg(cool_T, cool_X, smooth_window)
    title = experiment["specimen"].unique()[0]
    figs = []

    if interactive:
        _check_bokeh()
        bokeh_height = int(figsize[1] * 96)
        # Main plot
        p = figure(
            title=title,
            sizing_mode="stretch_width",
            height=bokeh_height,
            x_axis_label=f"Temperature (°{temp_unit})",
            y_axis_label="χ (m³ kg⁻¹)",
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )
        p.xaxis.axis_label_text_font_style = "normal"
        p.yaxis.axis_label_text_font_style = "normal"
        r_warm_c = p.scatter(
            warm_T, warm_X, legend_label="Heating",
            color="red", alpha=0.5, size=6,
        )
        r_warm_l = p.line(
            swT, swX, legend_label="Heating",
            line_width=2, color="red",
        )
        r_cool_c = p.scatter(
            cool_T, cool_X, legend_label="Cooling",
            color="blue", alpha=0.5, size=6,
        )
        r_cool_l = p.line(
            scT, scX, legend_label="Cooling",
            line_width=2, color="blue",
        )
        p.add_tools(
            HoverTool(renderers=[r_warm_c, r_warm_l],
                      tooltips=[("T", "@x"), ("Heating χ", "@y")])
        )
        p.add_tools(
            HoverTool(renderers=[r_cool_c, r_cool_l],
                      tooltips=[("T", "@x"), ("Cooling χ", "@y")])
        )
        p.grid.grid_line_color = "lightgray"
        p.outline_line_color = "black"
        p.background_fill_color = "white"
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        figs.append(p)

        # Derivative
        if plot_derivative:
            p_dx = figure(
                title=f"{title} – dχ/dT",
                sizing_mode="stretch_width",
                height=bokeh_height,
                x_axis_label=f"Temperature (°{temp_unit})",
                y_axis_label="dχ/dT",
                tools="pan,wheel_zoom,box_zoom,reset,save",
            )
            p_dx.xaxis.axis_label_text_font_style = "normal"
            p_dx.yaxis.axis_label_text_font_style = "normal"
            dx_w = np.gradient(swX, swT)
            dx_c = np.gradient(scX, scT)
            r_dx_w = p_dx.line(
                swT, dx_w, legend_label="Heating – dχ/dT",
                line_width=2, color="red"
            )
            r_dx_w_c = p_dx.scatter(
                swT, dx_w, legend_label="Heating – dχ/dT",
                color="red", alpha=0.5, size=6
            )
            r_dx_c = p_dx.line(
                scT, dx_c, legend_label="Cooling – dχ/dT",
                line_width=2, color="blue"
            )
            r_dx_c_c = p_dx.scatter(
                scT, dx_c, legend_label="Cooling – dχ/dT",
                color="blue", alpha=0.5, size=6
            )
            p_dx.add_tools(
                HoverTool(renderers=[r_dx_w, r_dx_w_c],
                          tooltips=[("T", "@x"), ("dχ/dT (heat)", "@y")])
            )
            p_dx.add_tools(
                HoverTool(renderers=[r_dx_c, r_dx_c_c],
                          tooltips=[("T", "@x"), ("dχ/dT (cool)", "@y")])
            )
            p_dx.grid.grid_line_color = "lightgray"
            p_dx.outline_line_color = "black"
            p_dx.background_fill_color = "white"
            p_dx.legend.location = "top_left"
            p_dx.legend.click_policy = "hide"
            figs.append(p_dx)

        # Inverse
        if plot_inverse:
            p_inv = figure(
                title=f"{title} – 1/χ",
                sizing_mode="stretch_width",
                height=bokeh_height,
                x_axis_label=f"Temperature (°{temp_unit})",
                y_axis_label="1/χ",
                tools="pan,wheel_zoom,box_zoom,reset,save",
            )
            p_inv.xaxis.axis_label_text_font_style = "normal"
            p_inv.yaxis.axis_label_text_font_style = "normal"
            swX_arr = np.array(swX)
            scX_arr = np.array(scX)
            inv_w = np.divide(1.0, swX_arr,
                              out=np.full_like(swX_arr, np.nan),
                              where=swX_arr != 0.0)
            inv_c = np.divide(1.0, scX_arr,
                              out=np.full_like(scX_arr, np.nan),
                              where=scX_arr != 0.0)
            mask_w = np.isfinite(inv_w)
            mask_c = np.isfinite(inv_c)
            r_inv_w = p_inv.line(
                np.array(swT)[mask_w], inv_w[mask_w],
                legend_label="Heating – 1/χ",
                line_width=2, color="red",
            )
            r_inv_w_c = p_inv.scatter(
                np.array(swT)[mask_w], inv_w[mask_w],
                color="red", alpha=0.5, size=6
            )
            r_inv_c = p_inv.line(
                np.array(scT)[mask_c], inv_c[mask_c],
                legend_label="Cooling – 1/χ",
                line_width=2, color="blue",
            )
            r_inv_c_c = p_inv.scatter(
                np.array(scT)[mask_c], inv_c[mask_c],
                color="blue", alpha=0.5, size=6
            )
            p_inv.add_tools(
                HoverTool(renderers=[r_inv_w, r_inv_w_c],
                          tooltips=[("T", "@x"), ("1/χ (heat)", "@y")])
            )
            p_inv.add_tools(
                HoverTool(renderers=[r_inv_c, r_inv_c_c],
                          tooltips=[("T", "@x"), ("1/χ (cool)", "@y")])
            )
            p_inv.grid.grid_line_color = "lightgray"
            p_inv.outline_line_color = "black"
            p_inv.background_fill_color = "white"
            p_inv.legend.location = "top_left"
            p_inv.legend.click_policy = "hide"
            figs.append(p_inv)

        for fig in figs:
            show(fig)

    else:
        fig_kwargs = {"figsize": figsize}
        fig1, ax1 = plt.subplots(**fig_kwargs)
        ax1.scatter(warm_T, warm_X, label="Heating", alpha=0.5)
        ax1.plot(swT, swX, label="Heating – smoothed", linewidth=2)
        ax1.scatter(cool_T, cool_X, label="Cooling", alpha=0.5)
        ax1.plot(scT, scX, label="Cooling – smoothed", linewidth=2)
        ax1.set_title(title)
        ax1.set_xlabel(f"Temperature (°{temp_unit})")
        ax1.set_ylabel("χ (m³ kg⁻¹)")
        ax1.grid(True)
        ax1.legend(loc="upper left")
        figs.append(fig1)

        if plot_derivative:
            dx_w = np.gradient(swX, swT)
            dx_c = np.gradient(scX, scT)
            fig2, ax2 = plt.subplots(**fig_kwargs)
            ax2.plot(swT, dx_w, label="Heating – dχ/dT", linewidth=2, marker="o")
            ax2.plot(scT, dx_c, label="Cooling – dχ/dT", linewidth=2, marker="o")
            ax2.set_title(f"{title} – dχ/dT")
            ax2.set_xlabel(f"Temperature (°{temp_unit})")
            ax2.set_ylabel("dχ/dT")
            ax2.grid(True)
            ax2.legend(loc="upper left")
            figs.append(fig2)

        if plot_inverse:
            swX_arr = np.array(swX)
            scX_arr = np.array(scX)
            inv_w = np.divide(
                1.0, swX_arr,
                out=np.full_like(swX_arr, np.nan),
                where=swX_arr != 0.0,
            )
            inv_c = np.divide(
                1.0, scX_arr,
                out=np.full_like(scX_arr, np.nan),
                where=scX_arr != 0.0,
            )
            mask_w = np.isfinite(inv_w)
            mask_c = np.isfinite(inv_c)
            fig3, ax3 = plt.subplots(**fig_kwargs)
            ax3.plot(np.array(swT)[mask_w], inv_w[mask_w], label="Heating – 1/χ", linewidth=2, marker="o")
            ax3.plot(np.array(scT)[mask_c], inv_c[mask_c], label="Cooling – 1/χ", linewidth=2, marker="o")
            ax3.set_title(f"{title} – 1/χ")
            ax3.set_xlabel(f"Temperature (°{temp_unit})")
            ax3.set_ylabel("1/χ")
            ax3.grid(True)
            ax3.legend(loc="upper left")
            figs.append(fig3)

        for fig in figs:
            plt.show(fig)

    if return_figure:
        return tuple(figs)
    return None

def estimate_curie_temperature(
    experiment,
    temperature_column="meas_temp",
    magnetic_column="susc_chi_mass",
    temp_unit="C",
    smooth_window=0,
    remove_holder=True,
    figsize=(6, 6),
    inverse_method=False,
    print_estimates=True
):
    """
    Estimate the Curie temperature from high temperature susceptibility curves in multiple ways. Automatically calculates first derivative minimum, second derivative maximum, and
    second derivative zero-crossing. Also has option to estimate Curie temperature from inverse susceptibility (E. Petrovsky and A. Kapicka, 2006). Uses Bokeh for the interactive plot.

    Parameters:
        experiment (pandas.DataFrame): MagIC-formatted experiment DataFrame.
        temperature_column (str): Name of temperature column.
        magnetic_column (str): Name of susceptibility column.
        temp_unit (str): "C" for Celsius.
        smooth_window (int): Window for smoothing, if 0, no smoothing is applied.
        remove_holder (bool): Subtracts holder signal to better isolate specimen signal.
        figsize (tuple): (width, height) in inches.
        inverse_method (bool): Use inverse susceptibility method.
        print_estimates (bool): Print estimated Curie temperatures.
    
    Returns
    -------

    temp_of_first_derivative_min_heating : float
        temperature of first derivative minimum for heating cycle
    temp_of_first_derivative_min_cooling : float
        temperature of first derivative minimum for cooling cycle
    temp_of_second_derivative_max_heating : float
        temperature of second derivative maximum for heating cycle
    temp_of_second_derivative_max_cooling : float
        temperature of second derivative maximum for cooling cycle
    heating_zero : list of float or None
        temperatures of second derivative zero-crossings for heating cycle, or None if none found
    cooling_zero : list of float or None
        temperatures of second derivative zero-crossings for cooling cycle, or None if none found
    """

    warm_T, warm_X, cool_T, cool_X = split_warm_cool(
        experiment,
        temperature_column=temperature_column,
        magnetic_column=magnetic_column
    )

    if temp_unit == "C":
        warm_T = [T - 273.15 for T in warm_T]
        cool_T = [T - 273.15 for T in cool_T]
    else:
        raise ValueError('temp_unit must be "C"')

    if remove_holder:
        holder_w = min(warm_X)
        holder_c = min(cool_X)
        warm_X = [X - holder_w for X in warm_X]
        cool_X = [X - holder_c for X in cool_X]

    swT, swX = smooth_moving_avg(warm_T, warm_X, smooth_window)
    scT, scX = smooth_moving_avg(cool_T, cool_X, smooth_window)

    dx_w = np.gradient(swX, swT)
    dx_c = np.gradient(scX, scT)

    temp_of_first_derivative_min_heating = swT[np.argmin(dx_w)]
    temp_of_first_derivative_min_cooling = scT[np.argmin(dx_c)]

    dx_2_w = np.gradient(dx_w, swT)
    dx_2_c = np.gradient(dx_c, scT)

    temp_of_second_derivative_max_heating = swT[np.argmax(dx_2_w)]
    temp_of_second_derivative_max_cooling = scT[np.argmax(dx_2_c)]

    # Physically consistent zero-crossing logic for heating
    min_idx_w = np.argmin(dx_2_w)
    max_idx_w = np.argmax(dx_2_w)
    lower_w, upper_w = sorted([min_idx_w, max_idx_w])
    dx2_slice_w = dx_2_w[lower_w:upper_w]
    temp_slice_w = swT[lower_w:upper_w]
    crossings_w = np.where(np.diff(np.sign(dx2_slice_w)))[0]
    temp_of_zero_crossing_heating = [temp_slice_w[i] for i in crossings_w]

    # Physically consistent zero-crossing logic for cooling
    min_idx_c = np.argmin(dx_2_c)
    max_idx_c = np.argmax(dx_2_c)
    lower_c, upper_c = sorted([min_idx_c, max_idx_c])
    dx2_slice_c = dx_2_c[lower_c:upper_c]
    temp_slice_c = scT[lower_c:upper_c]
    crossings_c = np.where(np.diff(np.sign(dx2_slice_c)))[0]
    temp_of_zero_crossing_cooling = [temp_slice_c[i] for i in crossings_c]

    if inverse_method:
        _check_bokeh()
        bokeh_height = int(figsize[1] * 96)
        title = experiment["specimen"].unique()[0]
        swX_arr = np.array(swX)
        inv_w = np.divide(1.0, swX_arr, out=np.full_like(swX_arr, np.nan), where=swX_arr != 0.0)
        mask_w = np.isfinite(inv_w)
        T = np.array(swT)[mask_w]
        inv_chi = inv_w[mask_w]

        # Creates initial fit endpoints (choose two points in the linear region)
        # 0.7 is Magic Number which places initial fit near expected linear region
        fit_x = [T[int(len(T)*0.7)], T[-1]]
        fit_y = [inv_chi[int(len(inv_chi)*0.7)], inv_chi[-1]]
        fit_source = ColumnDataSource(data=dict(x=fit_x, y=fit_y))
        # scatter and line for data
        data_source = ColumnDataSource(data=dict(x=T, y=inv_chi))
        p_inv = figure(title=f"{title} – 1/χ",
                       height=bokeh_height,
                       x_axis_label=f"Temperature (°{temp_unit})",
                       y_axis_label="1/χ",
                       tools="pan,wheel_zoom,box_zoom,reset,save",
                      )
        p_inv.scatter('x', 'y', source=data_source, size=8, color="red", legend_label="Heating – 1/χ")
        renderer = p_inv.scatter('x', 'y', source=fit_source, size=12, color="blue", legend_label="Fit Endpoints")
        p_inv.line('x', 'y', source=fit_source, line_width=2, color="blue", legend_label="Fit Line")
        # PointDrawTool for dragging endpoints
        draw_tool = PointDrawTool(renderers=[renderer], add=False)
        p_inv.add_tools(draw_tool)
        p_inv.toolbar.active_tap = draw_tool
        p_inv.legend.location = "top_left"   
        # Div to display Curie temperature
        curie_estimate = Div(text="Curie temperature: --", styles={'font-size': '16px', 'color': 'darkred'})  
        # JS callback to update fit line and Curie temperature estimate
        callback = CustomJS(args=dict(source=fit_source, div=curie_estimate), code="""
            var x = source.data.x;
            var y = source.data.y;
            if (x.length == 2) {
                var slope = (y[1] - y[0]) / (x[1] - x[0]);
                var intercept = y[0] - slope * x[0];
                // Estimate Curie temperature: x where y=0
                var Tc = -intercept / slope;
                div.text = "Curie temperature estimate: " + Tc.toFixed(2) + " °C";
            }
        """)
        fit_source.js_on_change('data', callback)       
        show(column(p_inv, curie_estimate))

    if print_estimates:
        print(f'First derivative minimum is at T={int(temp_of_first_derivative_min_heating)} for heating')
        print(f'First derivative minimum is at T={int(temp_of_first_derivative_min_cooling)} for cooling')
        print(f'Second derivative maximum is at T={int(temp_of_second_derivative_max_heating)} for heating')
        print(f'Second derivative maximum is at T={int(temp_of_second_derivative_max_cooling)} for cooling')
        if temp_of_zero_crossing_heating:  
            print(f'The second derivative of the heating curve crosses zero at T = {int(temp_of_zero_crossing_heating[0])}')  
        else:  
            print('No zero crossing found for the second derivative of the heating curve.')  
        if temp_of_zero_crossing_cooling:  
            print(f'The second derivative of the cooling curve crosses zero at T = {int(temp_of_zero_crossing_cooling[0])}')  
        else:
            print('No zero crossing found for the second derivative of the cooling curve.')

    heating_zero = temp_of_zero_crossing_heating[0] if temp_of_zero_crossing_heating else None
    cooling_zero = temp_of_zero_crossing_cooling[0] if temp_of_zero_crossing_cooling else None

    return (
        temp_of_first_derivative_min_heating,
        temp_of_first_derivative_min_cooling,
        temp_of_second_derivative_max_heating,
        temp_of_second_derivative_max_cooling,
        heating_zero,
        cooling_zero
    )

def smooth_moving_avg(
    x,
    y,
    x_window,
    window_type="hanning",
    pad_mode="edge",
    return_variance=False,
):
    """
    Smooth y vs x using an x-space moving window and numpy window functions.

    Parameters:
        x (array-like):
            1-D sequence of independent variable values.
        y (array-like):
            1-D sequence of dependent variable values.
        x_window (float):
            Width of the x-window centered on each point; must be >= 0.
            If zero, no smoothing is applied.
        window_type (str, optional):
            One of ['flat', 'hanning', 'hamming', 'bartlett', 'blackman'].
            'flat' is a simple running mean. Defaults to 'hanning'.
        pad_mode (str, optional):
            Mode for numpy.pad to reduce edge artifacts (e.g., 'edge',
            'constant', 'nearest'). Defaults to 'edge'.
        return_variance (bool, optional):
            If True, return weighted variances of x and y as well.
            Otherwise, only return smoothed x and y. Defaults to False.

    Returns:
        smoothed_x, smoothed_y (, x_var, y_var)
    """
    # convert to numpy arrays
    x = np.asarray(x)
    y = np.asarray(y)

    # validate dimensions
    if x.ndim != 1 or y.ndim != 1 or x.size != y.size:
        raise ValueError("`x` and `y` must be 1-D arrays of equal length.")

    # handle non-positive window
    if x_window < 0:
        raise ValueError("`x_window` must be non-negative.")
    if x_window == 0:
        if return_variance:
            x_var = np.zeros_like(x, dtype=float)
            y_var = np.zeros_like(y, dtype=float)
            return x, y, x_var, y_var
        return x, y

    # always pad to handle edge effects
    pad_n = x.size
    x_arr = np.pad(x, pad_n, mode=pad_mode)
    y_arr = np.pad(y, pad_n, mode=pad_mode)

    n = x.size
    sm_x = np.empty(n)
    sm_y = np.empty(n)
    if return_variance:
        x_var = np.empty(n)
        y_var = np.empty(n)
    half = x_window / 2.0

    for i, center in enumerate(x):
        mask = (x_arr >= center - half) & (x_arr <= center + half)
        idx = np.nonzero(mask)[0]
        if idx.size:
            xx = x_arr[idx]
            yy = y_arr[idx]
            m = idx.size
            if window_type == "flat":
                w = np.ones(m)
            else:
                w = getattr(np, window_type)(m)
            wsum = w.sum()
            mean_x = (w * xx).sum() / wsum
            mean_y = (w * yy).sum() / wsum
            if return_variance:
                vx = (w * (xx - mean_x) ** 2).sum() / wsum
                vy = (w * (yy - mean_y) ** 2).sum() / wsum
        else:
            mean_x = center
            mean_y = y[i]
            if return_variance:
                vx = vy = 0.0

        sm_x[i] = mean_x
        sm_y[i] = mean_y
        if return_variance:
            x_var[i] = vx
            y_var[i] = vy

    if return_variance:
        return sm_x, sm_y, x_var, y_var
    return sm_x, sm_y


def X_T_running_average(temp_list, chi_list, temp_window):
    """
    Compute running averages and variances of susceptibility over a sliding
    temperature window.

    Parameters
    ----------
    temp_list : Sequence[float]
        Ordered list of temperatures (must be same length as chi_list).
    chi_list : Sequence[float]
        List of susceptibility values corresponding to each temperature.
    temp_window : float
        Total width of the temperature window. Each point averages data in
        [T_i - temp_window/2, T_i + temp_window/2].

    Returns
    -------
    avg_temps : List[float]
        The mean temperature in each window (one per input point).
    avg_chis : List[float]
        The mean susceptibility in each window.
    temp_vars : List[float]
        The variance of temperatures in each window.
    chi_vars : List[float]
        The variance of susceptibility values in each window.
    """
    if not temp_list or not chi_list or temp_window <= 0:
        return temp_list, chi_list, [], []
    
    avg_temps = []
    avg_chis = []
    temp_vars = []
    chi_vars = []
    n = len(temp_list)
    
    for i in range(n):
        # Determine the temperature range for the current point
        temp_center = temp_list[i]
        start_temp = temp_center - temp_window / 2
        end_temp = temp_center + temp_window / 2
        
        # Get the indices within the temperature range
        indices = [j for j, t in enumerate(temp_list) if start_temp <= t <= end_temp]
        
        # Calculate the average temperature and susceptibility for the current window
        if indices:
            temp_range = [temp_list[j] for j in indices]
            chi_range = [chi_list[j] for j in indices]
            avg_temp = sum(temp_range) / len(temp_range)
            avg_chi = sum(chi_range) / len(chi_range)
            temp_var = np.var(temp_range)
            chi_var = np.var(chi_range)
        else:
            avg_temp = temp_center
            avg_chi = chi_list[i]
            temp_var = 0
            chi_var = 0
        
        avg_temps.append(avg_temp)
        avg_chis.append(avg_chi)
        temp_vars.append(temp_var)
        chi_vars.append(chi_var)
    
    return avg_temps, avg_chis, temp_vars, chi_vars


def optimize_moving_average_window(experiment, min_temp_window=0, max_temp_window=50, steps=50, colormapwarm='tab20b', colormapcool='tab20c'):
    """
    Visualize and optimize the moving average window size for smoothing experimental temperature-dependent data.

    This function evaluates the effect of different moving average window sizes on the smoothing of both the warm and cool cycles
    of an experiment (such as low temperature remanence or thermal demagnetization data). It iterates over a range of window sizes,
    applies smoothing, and computes the average variance and root mean square (RMS) for each window. These metrics are plotted
    to help the user visually identify the optimal window size for minimizing variance and RMS, balancing noise reduction and signal fidelity.

    Parameters
    ----------
    experiment : object or structured array
        Experimental data containing temperature and measurement values. It must be compatible with the `split_warm_cool` function.
    min_temp_window : float, optional
        Minimum window size (in degrees Celsius) for the moving average. Default is 0.
    max_temp_window : float, optional
        Maximum window size (in degrees Celsius) for the moving average. Default is 50.
    steps : int, optional
        Number of window size steps to evaluate between the minimum and maximum. Default is 50.
    colormapwarm : str, optional
        Matplotlib colormap name for the warm cycle plot. Default is 'tab20b'.
    colormapcool : str, optional
        Matplotlib colormap name for the cool cycle plot. Default is 'tab20c'.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib Figure object containing the optimization plots.
    axs : numpy.ndarray of matplotlib.axes.Axes
        Array of Axes objects (one for the warm cycle, one for the cool cycle).

    Examples
    --------
    >>> fig, axs = optimize_moving_average_window(my_experiment, min_temp_window=5, max_temp_window=30, steps=20)
    >>> fig.show()
    """
    warm_T, warm_X, cool_T, cool_X = split_warm_cool(experiment)
    windows = np.linspace(min_temp_window, max_temp_window, steps)
    fig, axs = plt.subplots(ncols=2, nrows=1, figsize=(12, 6))

    # Normalize the colormap
    norm = colors.Normalize(vmin=min_temp_window, vmax=max_temp_window)

    for window in windows:
        _, warm_avg_chis, _, warm_chi_vars = smooth_moving_avg(warm_T, warm_X, window, return_variance=True)
        warm_avg_rms, warm_avg_variance = calculate_avg_variance_and_rms(warm_X, warm_avg_chis, warm_chi_vars)
        _, cool_avg_chis, _, cool_chi_vars = smooth_moving_avg(cool_T, cool_X, window, return_variance=True)  
        cool_avg_rms, cool_avg_variance = calculate_avg_variance_and_rms(cool_X, cool_avg_chis, cool_chi_vars)

        axs[0].scatter(warm_avg_variance, warm_avg_rms, c=window, cmap=colormapwarm, norm=norm)
        axs[1].scatter(cool_avg_variance, cool_avg_rms, c=window, cmap=colormapcool, norm=norm)
        # ax.text(warm_avg_variance, warm_avg_rms, f'{window:.2f}°C', fontsize=12, ha='right')
        # ax.text(cool_avg_variance, cool_avg_rms, f'{window:.2f}°C', fontsize=12, ha='right')
    for ax in axs:
        ax.set_xlabel('Average Variance', fontsize=14)
        ax.set_ylabel('Average RMS', fontsize=14)
        
        ax.invert_yaxis()
    # show the colormaps and make sure the range is correct
    warm_cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=colormapwarm, norm=norm), orientation='horizontal', ax=axs[0])
    warm_cbar.set_label('Warm cycle window size (°C)')
    cool_cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=colormapcool, norm=norm), orientation='horizontal', ax=axs[1])
    cool_cbar.set_label('Cool cycle window size (°C)')
    plt.suptitle('Optimization of running average window size', fontsize=16)
    return fig, axs


def calculate_avg_variance_and_rms(chi_list, avg_chis, chi_vars):
    """
    Calculate the average root mean square (RMS) deviation and average variance for a set of measurements.

    This function computes two statistical metrics for a given list of measurement values and their corresponding
    moving averages and variances:
      1. The average RMS deviation, which quantifies the typical deviation between each measurement and its local average.
      2. The average variance, representing the mean of the provided variances for the measurements.

    Parameters
    ----------
    chi_list : array-like
        List or array of measurement values (e.g., susceptibility, magnetization).
    avg_chis : array-like
        List or array of moving average values corresponding to `chi_list`.
    chi_vars : array-like
        List or array of variance values for each measurement.

    Returns
    -------
    avg_rms : float
        The average root mean square deviation between each value in `chi_list` and its corresponding `avg_chis`.
    avg_variance : float
        The average of all values in `chi_vars`.

    Examples
    --------
    >>> chi = [1.0, 2.0, 3.0]
    >>> avg_chi = [0.9, 2.1, 2.9]
    >>> vars = [0.01, 0.02, 0.03]
    >>> avg_rms, avg_var = calculate_avg_variance_and_rms(chi, avg_chi, vars)
    >>> print(f"Average RMS: {avg_rms:.3f}, Average Variance: {avg_var:.3f}")
    """
    rms_list = np.sqrt([(chi - avg_chi)**2 for chi, avg_chi in zip(chi_list, avg_chis)])
    total_rms = np.sum(rms_list)
    avg_rms = total_rms / len(rms_list)
    
    total_variance = np.sum(chi_vars)
    avg_variance = total_variance / len(chi_vars)
    
    return avg_rms, avg_variance


# backfield data processing functions
# ------------------------------------------------------------------------------------------------------------------
def backfield_data_processing(experiment, field='treat_dc_field', magnetization='magn_mass', smooth_mode='lowess', smooth_frac=0.0, drop_first=False):
    '''
    Function to process the backfield data including shifting the magnetic 
    moment to be positive values taking the log base 10 of the magnetic 
    field values and writing these new fields into the experiment attribute 
    table

    Parameters
    ----------
    experiment : DataFrame
        DataFrame containing the backfield data
    field : str
        The name of the treatment field column in the DataFrame
    magnetization : str
        The name of the magnetization column in the DataFrame
    smooth_mode : str
        The smoothing mode to be used, either 'lowess' or 'spline'
    smooth_frac : float
        Fraction of the data to be used for LOWESS smoothing, value must be between 0 and 1
    drop_first : bool
        Whether to drop the first data point or not
        in some cases you may want to drop the first data point to avoid negative log values
    
    Returns
    -------
    DataFrame
        The processed experiment DataFrame with new attributes.
    '''
    assert smooth_mode in ['lowess', 'spline'], 'smooth_mode must be either lowess or spline'
    assert smooth_frac >= 0 and smooth_frac <= 1, 'smooth_frac must be between 0 and 1'
    assert isinstance(drop_first, bool), 'drop_first must be a boolean'
    
    experiment = experiment.reset_index(drop=True)
    # check and make sure to force drop first row if the first treat field is in the wrong direction
    if experiment[field].iloc[0] > 0:
        drop_first = True
    if drop_first:
        experiment = experiment.iloc[1:].reset_index(drop=1)
    
    if find_y_crossing(experiment[field], experiment[magnetization]) is not None:
        Bcr = np.abs(find_y_crossing(experiment[field], experiment[magnetization]))
    else:
        Bcr = np.nan
    # to plot the backfield data in the conventional way, we need to shift the magnetization to be positive
    experiment['magn_mass_shift'] = [i - experiment[magnetization].min() for i in experiment[magnetization]]
    # we then calculate the log10 of the treatment fields
    experiment['log_dc_field'] = np.log10(-experiment[field]*1e3)
    if smooth_mode == 'spline':
        # spline smoothing
        x = experiment['log_dc_field']
        y = experiment['magn_mass_shift']
        y_mean = np.mean(y)
        y_std = np.std(y)
        y_scaled = (y - y_mean) / y_std

        # Map it to actual s value
        s = smooth_frac * len(x) * y_mean

        spl = UnivariateSpline(x, y_scaled, s=s)
        experiment['smoothed_magn_mass_shift'] = spl(x) * y_std + y_mean
        experiment['smoothed_log_dc_field'] = x
    elif smooth_mode == 'lowess':
        _check_statsmodels()
        spl = lowess(experiment['magn_mass_shift'], experiment['log_dc_field'], frac=smooth_frac)
        experiment['smoothed_magn_mass_shift'] = spl[:, 1]
        experiment['smoothed_log_dc_field'] = spl[:, 0]
    return experiment, Bcr
    
    
def plot_backfield_data(
    experiment,
    field="treat_dc_field",
    magnetization="magn_mass",
    Bcr=None,
    figsize=(5, 10),
    plot_raw=True,
    plot_processed=True,
    plot_spectrum=True,
    interactive=False,
    return_figure=False,
    show_plot=True,
    y_axis_units="Am²/kg",
    legend_location="upper left"
):
    """
    Plot backfield data: raw, processed, and coercivity spectrum.

    Parameters
    ----------
    experiment : DataFrame
        Must contain raw and, if requested, processed columns.
    field : str
        Name of the magnetic field column.
    magnetization : str
        Name of the magnetization column.
    Bcr : float, optional
        Calculated Bcr (T). If provided, will be plotted as a pink star.
    figsize : tuple(float, float)
        Figure size (in inches).
    plot_raw : bool
    plot_processed : bool
    plot_spectrum : bool
    interactive : bool
    return_figure : bool
    show_plot : bool
    y_axis_units : str, optional
        Units to display on the y-axis labels of raw and processed panels.
    legend_location : str, optional
        Location of the legend in Matplotlib terms.

    Returns
    -------
    Matplotlib (fig, axes) or Bokeh grid or None
    """
    # Check columns
    req = []
    if plot_raw:
        req += [field, magnetization]
    if plot_processed or plot_spectrum:
        req += [
            "log_dc_field",
            "magn_mass_shift",
            "smoothed_log_dc_field",
            "smoothed_magn_mass_shift",
        ]
    missing = [c for c in req if c not in experiment.columns]
    if missing:
        raise KeyError(f"Missing columns: {missing}")

    # Prepare spectrum
    if plot_spectrum:
        log_b = experiment["log_dc_field"]
        shift_m = experiment["magn_mass_shift"]
        raw_dy = -np.diff(shift_m) / np.diff(log_b)
        raw_dx_log = log_b.rolling(2).mean().dropna()
        smooth_dy = -np.diff(experiment["smoothed_magn_mass_shift"]) / np.diff(
            experiment["smoothed_log_dc_field"]
        )
        smooth_dx_log = experiment["smoothed_log_dc_field"].rolling(2).mean().dropna()
        raw_dx = 10 ** raw_dx_log
        smooth_dx = 10 ** smooth_dx_log

    # Interactive: Bokeh
    if interactive:
        _check_bokeh()
        tools = [
            HoverTool(tooltips=[("Field (T)", "@x"), ("Mag", "@y")]),
            "pan,box_zoom,wheel_zoom,reset,save"
        ]
        figs = []
        palette = Category10[4]
        bokeh_height = int(figsize[1] / 3 * 96)

        if plot_raw:
            p0 = figure(
                title="Raw backfield",
                x_axis_label="Field (T)",
                y_axis_label=f"Magnetization ({y_axis_units})",
                tools=tools,
                sizing_mode="stretch_width",
                height=bokeh_height,
            )
            p0.scatter(
                experiment[field],
                experiment[magnetization],
                legend_label="raw",
                color=palette[0],
                size=6,
            )
            p0.line(experiment[field], experiment[magnetization], color=palette[0])
            if Bcr is not None and not np.isnan(Bcr):
                p0.scatter(
                    [-Bcr],
                    0,
                    size=15,
                    color="pink",
                    marker="star",
                    line_color="black",
                    legend_label=f"Bcr = {Bcr:.5f} T",
                )
            p0.xaxis.axis_label_text_font_style = "normal"
            p0.yaxis.axis_label_text_font_style = "normal"
            p0.legend.location = map_legend_location(legend_location)
            p0.legend.click_policy = "hide"
            figs.append(p0)

        if plot_processed:
            x_shifted = 10 ** experiment["log_dc_field"]
            x_smooth = 10 ** experiment["smoothed_log_dc_field"]
            p1 = figure(
                title="Processed backfield",
                x_axis_label="Field (mT)",
                y_axis_label=f"Magnetization ({y_axis_units})",
                x_axis_type="log",
                tools=tools,
                sizing_mode="stretch_width",
                height=bokeh_height,
            )
            p1.scatter(
                x_shifted,
                experiment["magn_mass_shift"],
                legend_label="shifted",
                color=palette[1],
                size=6,
            )
            p1.line(
                x_smooth,
                experiment["smoothed_magn_mass_shift"],
                color=palette[1],
                legend_label="smoothed",
            )
            p1.xaxis.axis_label_text_font_style = "normal"
            p1.yaxis.axis_label_text_font_style = "normal"
            p1.legend.location = map_legend_location(legend_location)
            p1.legend.click_policy = "hide"
            figs.append(p1)

        if plot_spectrum:
            p2 = figure(
                title="Coercivity spectrum",
                x_axis_label="Field (mT)",
                y_axis_label="dM/dlog(B)",
                x_axis_type="log",
                tools=tools,
                sizing_mode="stretch_width",
                height=bokeh_height,
            )
            p2.scatter(raw_dx, raw_dy, legend_label="raw spectrum",
                       color=palette[2], size=6)
            p2.line(smooth_dx, smooth_dy, color=palette[2],
                    legend_label="smoothed spectrum")
            p2.xaxis.axis_label_text_font_style = "normal"
            p2.yaxis.axis_label_text_font_style = "normal"
            p2.legend.location = map_legend_location(legend_location)
            p2.legend.click_policy = "hide"
            figs.append(p2)

        grid = gridplot(figs, ncols=1, sizing_mode="stretch_width")
        if show_plot:
            show(grid)
        if return_figure:
            return grid
        return None

    # Static: Matplotlib
    panels = []
    if plot_raw:
        panels.append("raw")
    if plot_processed:
        panels.append("processed")
    if plot_spectrum:
        panels.append("spectrum")

    n = len(panels)
    fig, axes = plt.subplots(nrows=n, ncols=1, figsize=figsize)
    if n == 1:
        axes = [axes]

    for ax, panel in zip(axes, panels):
        if panel == "raw":
            ax.scatter(
                experiment[field], experiment[magnetization], c="k", s=10, label="raw"
            )
            ax.plot(experiment[field], experiment[magnetization], c="k")
            if Bcr is not None and not np.isnan(Bcr):
                y_min = experiment[magnetization].min()
                y_max = experiment[magnetization].max()
                y_mid = y_min + 0.5 * (y_max - y_min)
                ax.scatter(
                    -Bcr,
                    y_mid,
                    marker="*",
                    s=150,
                    c="pink",
                    edgecolors="black",
                    label=f"Bcr = {Bcr:.5f} T",
                    zorder=10,
                )
            ax.set(
                title="raw backfield",
                xlabel="field (T)",
                ylabel=f"magnetization ({y_axis_units})",
            )
            ax.legend(loc=legend_location)
        elif panel == "processed":
            ax.scatter(
                experiment["log_dc_field"],
                experiment["magn_mass_shift"],
                c="gray",
                s=10,
                label="shifted",
            )
            ax.plot(
                experiment["smoothed_log_dc_field"],
                experiment["smoothed_magn_mass_shift"],
                c="k",
                label="smoothed",
            )
            ticks = ax.get_xticks()
            ax.set_xticklabels([f"{round(10**t, 1)}" for t in ticks])
            ax.set(
                title="processed",
                xlabel="field (mT)",
                ylabel=f"magnetization ({y_axis_units})",
            )
            ax.legend(loc=legend_location)
        else:  # spectrum
            ax.scatter(raw_dx_log, raw_dy, c="gray", s=10, label="raw spectrum")
            ax.plot(smooth_dx_log, smooth_dy, c="k", label="smoothed spectrum")
            ticks = ax.get_xticks()
            ax.set_xticklabels([f"{round(10**t, 1)}" for t in ticks])
            ax.set(title="spectrum", xlabel="field (mT)", ylabel="dM/dlog(B)")
            ax.legend(loc=legend_location)

    fig.tight_layout()
    if show_plot:
        plt.show()
    if return_figure:
        return fig, axes
    return None


def backfield_unmixing(field, magnetization, n_comps=1, parameters=None, iter=True, n_iter=3, skewed=True):
    '''
    backfield unmixing for a single experiment

    Parameters
    ----------
    field : np.array
        The field values in log10 unit in the experiment
    magnetization : np.array
        The magnetization values in the experiment
    n_comps : int
        Number of components to unmix the data into
    params : Pandas DataFrame
        Initial values for the model parameters
        should be constructed as the following columns:
        - amplitude in arbitrary scale
        - center in unit of mT
        - sigma in unit of mT
        - gamma in arbitrary scale
        |amplitude|center|sigma|gamma|
        |---|---|---|---|
        |1.0|100|10|0.0|
        |...|...|...|...|
        the program will automatically go through the rows and extract these inital parameter values
        If the parameters are not given, we will run an automated program to make initial guess

    iter : bool
        Whether to iterate the fitting process or not. It is useful to iterate the fitting process
        to make sure the parameters are converged
    n_iter : int
        Number of iterations to run the fitting process
    skewed : bool
        Whether to use skewed Gaussian model or not
        if False, the program will use normal Gaussian model
    
    Returns
    -------
    result : lmfit.model.ModelResult
        The result of the fitting process
    parameters : DataFrame
        The updated parameters table
    '''
    _check_lmfit()
    assert n_comps > 0, 'n_component must be greater than 0'
    assert isinstance(n_comps, int), 'n_component must be an integer'
    assert isinstance(parameters, pd.DataFrame), f"Expected a pandas DataFrame, but got {type(parameters).__name__}"
    assert n_comps == parameters.shape[0], 'number of components must match the number of rows in the parameters table'
    assert n_iter > 0, 'n_iter must be greater than 0'

    # Ensure the parameter columns are float. The fit updates below write
    # floats back into these columns in place; if the caller passes integer
    # initial guesses (as the docstring example does), the columns are int
    # dtype and pandas >= 3.0 raises when a float is assigned into them.
    for col in ['amplitude', 'center', 'sigma', 'gamma']:
        if col in parameters.columns:
            parameters[col] = parameters[col].astype(float)

    if not iter:
        n_iter = 1

    # re-calculate the derivatives based on the smoothed data columns
    smoothed_derivatives_y = -np.diff(magnetization)/np.diff(field)
    smoothed_derivatives_x = pd.Series(field).rolling(window=2).mean().dropna()

    # create the model depending on the number of components specified
    composite_model = None
    params = Parameters()
    for i in range(n_comps):
        prefix = f'g{i+1}_'
        model = SkewedGaussianModel(prefix=prefix)
        
        # Initial parameter guesses
        params.add(f'{prefix}amplitude', value=parameters['amplitude'][i])
        params.add(f'{prefix}center', value=np.log10(parameters['center'][i]))
        params.add(f'{prefix}sigma', value=np.log10(parameters['sigma'][i]))
        params.add(f'{prefix}gamma', value=parameters['gamma'][i])
        
        # now let's set bounds to the parameters to help fitting algorithm converge
        params[f'{prefix}amplitude'].min = 0  # Bounds for amplitude parameters
        params[f'{prefix}amplitude'].max = 1 # Bounds for proportion/amplitude parameters
        params[f'{prefix}center'].min = np.min(field)  # Bounds for center parameters
        params[f'{prefix}center'].max = np.max(field) # Bounds for center parameters
        params[f'{prefix}sigma'].min = 0
        params[f'{prefix}sigma'].max = np.max(field)-np.min(field)   # Bounds for sigma parameters

        # restrict to normal distribution if skewed is False
        if not skewed:
            params[f'{prefix}gamma'].set(value=0, vary=False)

        if composite_model is None:
            composite_model = model
        else:
            composite_model += model

    def fitting_function(y, params, x):
        result = composite_model.fit(y, params, x=x)
        for i in range(n_comps):
            prefix = f'g{i+1}_'
            parameters.loc[i, 'amplitude'] = result.params[f'{prefix}amplitude'].value # convert back to original scale
            parameters.loc[i, 'center'] = 10**result.params[f'{prefix}center'].value # convert back to mT
            parameters.loc[i, 'sigma'] = 10**result.params[f'{prefix}sigma'].value # convert back to mT
            parameters.loc[i, 'gamma'] = result.params[f'{prefix}gamma'].value
        return result, parameters

    result, parameters = fitting_function(smoothed_derivatives_y/np.max(smoothed_derivatives_y), params, x=smoothed_derivatives_x)

    if iter:
        for i in range(n_iter):
            result, parameters = fitting_function(smoothed_derivatives_y/np.max(smoothed_derivatives_y), result.params, x=smoothed_derivatives_x)

    return result, parameters


def plot_backfield_unmixing_result(experiment, result, sigma=2, figsize=(8,6), n=200):
    '''
    function for plotting the backfield unmixing results

    Parameters
    ----------
    experiment : pandas.DataFrame
        the backfield experiment data
    result : lmfit.model.ModelResult
        the result of the backfield unmixing
    sigma : float
        the sigma value for the uncertainty band
    figsize : tuple
        the figure size
    n : int
        the number of points for the x-axis interpolation
        you may choose a large enough number so that the result components 
        and the best fit curves are smooth
        
    Returns
    -------
    fig : matplotlib.figure.Figure
        the figure object
    ax : matplotlib.axes._axes.Axes
        the axes object
    '''
    raw_derivatives_y = -np.diff(experiment['magn_mass_shift'])/np.diff(experiment['log_dc_field'])
    raw_derivatives_x = experiment['log_dc_field'].rolling(window=2).mean().dropna()
    smoothed_derivatives_x = experiment['smoothed_log_dc_field'].rolling(window=2).mean().dropna()

    x_interp = np.linspace(smoothed_derivatives_x.min(), smoothed_derivatives_x.max(), n)
    best_fit_interp = result.eval(x=x_interp) * np.max(raw_derivatives_y)
    dely_interp = result.eval_uncertainty(x=x_interp, sigma=sigma) * np.max(raw_derivatives_y)
    # impose bounds on the dely to be smaller than the best fit
    dely_interp = [min(dely_interp[i], best_fit_interp[i]) for i in range(len(dely_interp))]
    fig, ax = plt.subplots(figsize=figsize)
    # first plot the scatter raw dMdB data
    ax.scatter(raw_derivatives_x, raw_derivatives_y, c='grey', marker='o', s=10, label='raw coercivity spectrum')
    # plot the total best fit
    ax.plot(x_interp, best_fit_interp, '-', color='k', alpha=0.6, label='total spectrum best fit')
    ax.fill_between(x_interp,
                    [max(best_fit_interp[j]-dely_interp[j],0) for j in range(len(best_fit_interp))],
                    best_fit_interp+dely_interp,
                    color="#8A8A8A", 
                    label=f'total {sigma}-$\sigma$ band', alpha=0.5)
    if len(result.components) > 1:
        for i in range(len(result.components)):
            this_comp_interp = result.eval_components(x=x_interp)[f'g{i+1}_'] * np.max(raw_derivatives_y)
            this_dely = result.dely_comps[f'g{i+1}_'] * np.max(raw_derivatives_y)
            # impose bounds on the dely to be smaller than the best fit for the component
            this_dely = [min(this_dely[j], this_comp_interp[j]) for j in range(len(this_dely))]
            ax.plot(x_interp, this_comp_interp, c=f'C{i}', label=f'component #{i+1}, {sigma}-$\sigma$ band')
            lower_bound = [max(this_comp_interp[j]-this_dely[j],0) for j in range(len(this_comp_interp))]
            upper_bound = this_comp_interp+this_dely
            ax.fill_between(x_interp,
                            lower_bound,
                            upper_bound,
                            color=f'C{i}', alpha=0.5)

    xticks = ax.get_xticks()
    ax.set_xticklabels([f'{int(10**i)}' for i in xticks])
    ax.legend()
    ax.set_title('coercivity unmixing results')
    ax.set_xlabel('treatment field (mT)', fontsize=14)
    ax.set_ylabel('dM/dlog(B)', fontsize=14)
    return fig, ax

def interactive_backfield_fit(field, magnetization, n_components, skewed=True, figsize=(10, 6)):
    """
    Function for interactive backfield unmixing using skew‑normal distributions.
    No uncertainty propagation is shown; this function is useful for estimating
    initial guesses for parameters.

    *Important note:* in a Jupyter notebook use the `%matplotlib widget`
    command to enable live figure updates.

    Parameters
    ----------
    field : array‑like
        The field values in log scale.
    magnetization : array‑like
        The magnetization values in log scale.
    n_components : int
        The number of skew‑normal components to fit.
    figsize : tuple, optional
        The size of the figure to display. Default is (10, 6).

    Returns
    -------
    pandas.DataFrame
        A DataFrame of the most recent fit parameters with columns
        `amplitude`, `center`, `sigma`, and `gamma`. This DataFrame is
        updated in place as sliders are moved.
    """
    
    _check_ipywidgets()
    _check_lmfit()
    final_fit = {"df": None}

    # Calculate the smoothed derivative
    smoothed_derivatives_y = -np.diff(magnetization) / np.diff(field)
    smoothed_derivatives_x = pd.Series(field).rolling(window=2).mean().dropna()

    fig, ax = plt.subplots(figsize=figsize)
    fig.canvas.header_visible = False

    # Store all sliders and text
    sliders = []
    texts = []

    def create_slider_dict(name, min_val, max_val, step, description, value=0.0):
        return {
            f"{name}_{i}": FloatSlider(
                value=value,
                min=min_val,
                max=max_val,
                step=step,
                description=f'{description}_{i+1}',
                continuous_update=False
            )
            for i in range(n_components)
        }

    amp_slidebars = create_slider_dict('amplitude', 0.0, 1, 0.01, 'amplitude')
    center_slidebars = create_slider_dict('center', 0.0, 10**np.max(field), 10**np.max(field) / 100, 'center', value=10**np.max(field)/2)
    sigma_slidebars = create_slider_dict('sigma', 0.0, 10**np.max(field), 10**np.max(field) / 100, 'sigma', value=10**np.max(field)/2)
    gamma_slidebars = create_slider_dict('gamma', -10.0, 10.0, 0.01, 'gamma')

    # Collect all sliders by component for display and registration

    for i in range(n_components):
        # Create sliders for each component
        amp_slider = amp_slidebars[f'amplitude_{i}']
        center_slider = center_slidebars[f'center_{i}']
        sigma_slider = sigma_slidebars[f'sigma_{i}']
        gamma_slider = gamma_slidebars[f'gamma_{i}']
        # Create a dictionary for each component
        d = {
            'amplitude': amp_slider,
            'center': center_slider,
            'sigma': sigma_slider,
            'gamma': gamma_slider
        }
        # Add sliders to the list
        if skewed:
            sliders.append(VBox([amp_slider, center_slider, sigma_slider, gamma_slider]))
        else:
            sliders.append(VBox([amp_slider, center_slider, sigma_slider]))

    # now add the same amount of text boxes to update the best fit parameters on the fly
    for i in range(n_components):
        # make text boxes for each parameter
        amp_text = widgets.Text(value=str(amp_slidebars[f'amplitude_{i}'].value), description=f'amplitude_{i+1}')
        center_text = widgets.Text(value=str(center_slidebars[f'center_{i}'].value), description=f'center_{i+1}')
        sigma_text = widgets.Text(value=str(sigma_slidebars[f'sigma_{i}'].value), description=f'sigma_{i+1}')
        gamma_text = widgets.Text(value=str(gamma_slidebars[f'gamma_{i}'].value), description=f'gamma_{i+1}')
        # add the text boxes to the texts list
        if skewed:
            texts.append(VBox([amp_text, center_text, sigma_text, gamma_text]))
        else:
            texts.append(VBox([amp_text, center_text, sigma_text]))

    # Display sliders
    display(HBox(sliders))
    display(HBox(texts))

    def update_plot(*args):
        ax.clear()
        ax.scatter(smoothed_derivatives_x, smoothed_derivatives_y, marker='o', s=5, alpha=0.5, color='grey', label='original data')
        ax.set_xlabel('Field', fontsize=12)
        ax.set_ylabel('dM/dlog(B)', fontsize=12)

        # Get values from sliders
        amp = [amp_slidebars[f'amplitude_{i}'].value  for i in range(n_components)]
        center = [center_slidebars[f'center_{i}'].value for i in range(n_components)]
        sigma = [sigma_slidebars[f'sigma_{i}'].value for i in range(n_components)]
        gamma = [gamma_slidebars[f'gamma_{i}'].value for i in range(n_components)]
        
        # Create a DataFrame for the parameters
        parameters = pd.DataFrame({
            'amplitude': amp,
            'center': center,
            'sigma': sigma,
            'gamma': gamma
        })

        result, updated_parameters = backfield_unmixing(field, magnetization, n_comps=n_components, parameters=parameters, skewed=skewed)
        # update the text boxes with the updated parameters
        for i in range(n_components):
            amp_text = texts[i].children[0]
            center_text = texts[i].children[1]
            sigma_text = texts[i].children[2]
            amp_text.value = str(updated_parameters['amplitude'][i].round(4))
            center_text.value = str(updated_parameters['center'][i].round(4))
            sigma_text.value = str(updated_parameters['sigma'][i].round(4))
            if skewed:
                gamma_text = texts[i].children[3]
                gamma_text.value = str(updated_parameters['gamma'][i].round(4))

        ax.plot(field, result.eval(x=field)*np.max(smoothed_derivatives_y), '-', color='k', alpha=0.6, label='total spectrum best fit')
        if len(result.components) > 1:
            for i in range(len(result.components)):
                this_comp = result.eval_components(x=field)[f'g{i+1}_']*np.max(smoothed_derivatives_y)
                ax.plot(field, this_comp, c=f'C{i}', label=f'component #{i+1}')

        ax.set_xticklabels([f'{int(10**i)}' for i in ax.get_xticks()])
        ax.legend()

        # fig.canvas.draw()
        fig.canvas.flush_events()
        if final_fit["df"] is None:
            final_fit["df"] = updated_parameters.copy()
        else:
            # overwrite the existing DataFrame’s values
            for col in updated_parameters.columns:
                final_fit["df"][col] = updated_parameters[col].values
        
    # Attach observers
    for box in sliders:
        for slider in box.children:
            if isinstance(slider, FloatSlider):
                slider.observe(update_plot, names='value')

    update_plot()
    return final_fit["df"]

def backfield_MaxUnmix(field, magnetization, n_comps=1, parameters=None, skewed=True, n_resample=100, proportion=0.95, figsize=(10, 6), random_seed=None):
    '''
    function for performing the MaxUnmix backfield unmixing algorithm
        The components are modelled as skew-normal distributions
        The uncertainties are calculated based on a bootstrap approach
            where the given data points are bootstrap resampled with replacement
            and the unmixing is done with the same original estimates for each iteration

    Parameters
    ----------
    field : array-like
        The field values in log10 scale
    magnetization : array-like
        The magnetization values
    parameters : DataFrame
        The parameters for the unmixing. The DataFrame should contain the following columns:
            'amplitude', 'center', 'sigma', 'gamma'
        The number of rows in the DataFrame should be equal to n_comps
    skewed : bool
        Whether to use skewed Gaussian model or not
        if not, the program will use normal Gaussian model
    n_resample : int, optional
        The number of bootstrap resamples. The default is 100.
    proportion : float, optional
        The proportion of the data to be used for the bootstrap resampling. The default is 0.95.
        The actual number of resampled points per iteration is calculated as int(len(field) * proportion)
    n_comps : int, optional
        The number of components to be used for the unmixing. The default is 1.
    random_seed : None, int, or numpy.random.Generator, optional
        Seed for reproducible bootstrap resampling (default None).
    '''
    _check_lmfit()
    assert parameters is not None, f"parameters should not be None"
    assert len(parameters) == n_comps, f"Number of rows in parameters ({len(parameters)}) should be equal to n_comps ({n_comps})"
    assert proportion > 0 and proportion <= 1, f"proportion should be between 0 and 1, but got {proportion}"

    rng = _resolve_rng(random_seed)

    field = np.array(field)
    magnetization = np.array(magnetization)
    dMdB = -np.diff(magnetization) / np.diff(field)
    B = pd.Series(field).rolling(window=2).mean().dropna().to_numpy()

    B_high_resolution = np.linspace(np.min(B), np.max(B), 200)
    # store the total dMdB fits
    all_total_dMdB = np.zeros((n_resample, len(B_high_resolution)))
    # store dMdB fits for each component
    all_component_dMdB = np.zeros((n_resample, n_comps, len(B_high_resolution)))
    # store distrbution parameters
    all_parameters = np.zeros((n_resample, n_comps, 4))
    for iter in range(n_resample):
        # bootstrap resample with replacement of the data
        index_resample = rng.choice(len(B), size=int(len(B) * proportion), replace=True)
        B_resample = B[index_resample]
        dMdB_resample = dMdB[index_resample]

        params = Parameters()
        # Create a composite model
        composite_model = None
        for i in range(n_comps):
            prefix = f'g{i+1}_'
            model = SkewedGaussianModel(prefix=prefix)
            # Initial parameter guesses
            params.add(f'{prefix}amplitude', value=parameters['amplitude'][i])
            params.add(f'{prefix}center', value=np.log10(parameters['center'][i]))
            params.add(f'{prefix}sigma', value=np.log10(parameters['sigma'][i]))
            params.add(f'{prefix}gamma', value=parameters['gamma'][i])
            
            # now let's set bounds to the parameters to help fitting algorithm converge
            params[f'{prefix}amplitude'].min = 0  # Bounds for amplitude parameters
            params[f'{prefix}amplitude'].max = 1 # Bounds for proportion/amplitude parameters
            params[f'{prefix}center'].min = np.min(B)  # Bounds for center parameters
            params[f'{prefix}center'].max = np.max(B) # Bounds for center parameters
            params[f'{prefix}sigma'].min = 0
            params[f'{prefix}sigma'].max = np.max(B)-np.min(B)   # Bounds for sigma parameters

            # restrict to normal distribution if skewed is False
            if not skewed:
                params[f'{prefix}gamma'].set(value=0, vary=False)
                
            if composite_model is None:
                composite_model = model
            else:
                composite_model += model
            
        result = composite_model.fit(dMdB_resample/np.max(dMdB_resample), params, x=B_resample)
        all_parameters[iter] = np.array([[result.params[f'g{i+1}_amplitude'].value,
                                          result.params[f'g{i+1}_center'].value,
                                          result.params[f'g{i+1}_sigma'].value,
                                          result.params[f'g{i+1}_gamma'].value] for i in range(n_comps)])
        all_total_dMdB[iter] = result.eval(x=B_high_resolution)*np.max(dMdB_resample)
        for j in range(n_comps):
            prefix = f'g{j+1}_'
            # get the component model
            this_comp = result.eval_components(x=B_high_resolution)[f'{prefix}']*np.max(dMdB_resample)
            # store the component model
            all_component_dMdB[iter][j] = this_comp
    # calculate the 2.5, 50, and 97.5 percentiles of the bootstrap resamples
    dMdB_2_5 = np.percentile(all_total_dMdB, 2.5, axis=0)
    dMdB_50 = np.percentile(all_total_dMdB, 50, axis=0)
    dMdB_97_5 = np.percentile(all_total_dMdB, 97.5, axis=0)

    # calculate the 2.5, 50, and 97.5 percentiles of the bootstrap resamples for each component
    dMdB_2_5_components = np.percentile(all_component_dMdB, 2.5, axis=0)
    dMdB_50_components = np.percentile(all_component_dMdB, 50, axis=0)
    dMdB_97_5_components = np.percentile(all_component_dMdB, 97.5, axis=0)

    # calculate the mean and std of the parameters; center and sigma are
    # fit in log10 space, so convert each bootstrap value to linear (mT)
    # units before taking the mean/std (10**std of log values is not a
    # standard deviation in mT)
    mean_parameters = np.mean(all_parameters, axis=0)
    std_parameters = np.std(all_parameters, axis=0)
    center_mT = 10 ** all_parameters[:, :, 1]
    sigma_mT = 10 ** all_parameters[:, :, 2]

    # report a dictionary of the mean and std of the parameters
    parameters_dict = {}
    for i in range(n_comps):
        this_parameters_dict = {
            f'g{i+1}_amplitude': mean_parameters[i][0],
            f'g{i+1}_center': np.mean(center_mT[:, i]),
            f'g{i+1}_sigma': np.mean(sigma_mT[:, i]),
            f'g{i+1}_gamma': mean_parameters[i][3],
            f'g{i+1}_amplitude_std': std_parameters[i][0],
            f'g{i+1}_center_std': np.std(center_mT[:, i]),
            f'g{i+1}_sigma_std': np.std(sigma_mT[:, i]),
            f'g{i+1}_gamma_std': std_parameters[i][3]
        }
        parameters_dict.update(this_parameters_dict)

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(B, dMdB, marker='o', s=5, alpha=0.5, color='grey', label='original data')
    ax.plot(B_high_resolution, dMdB_50, '-', color='k', alpha=0.6, label='total best fit')
    ax.fill_between(B_high_resolution, dMdB_2_5, dMdB_97_5, color='k', alpha=0.2, label='total 95% CI')
    # plot the components
    for k in range(n_comps):
        ax.plot(B_high_resolution, dMdB_50_components[k], c=f'C{k}', label=f'component #{k+1}')
        ax.fill_between(B_high_resolution, dMdB_2_5_components[k], dMdB_97_5_components[k], color=f'C{k}', alpha=0.2, label=f'component #{k+1} 95% CI')
    ax.set_xlabel('Field (mT)', fontsize=12)
    ax.set_ylabel('dM/dlog(B)', fontsize=12)
    ax.set_xticklabels([f'{int(10**i)}' for i in ax.get_xticks()])
    ax.legend()
    fig.canvas.header_visible = False  
    
    return ax, parameters_dict


def add_unmixing_stats_to_specimens_table(specimens_df, experiment_name, unmix_result, method='lmfit'):
    '''
    function to export the hysteresis data to a MagIC specimen data table
    
    Parameters
    ----------
    specimens_df : pd.DataFrame
        dataframe with the specimen data
    experiment_name : str
        name of the experiment
    unmix_result : dict
        dictionary with the unmixing results
        as output from rmag.backfield_MaxUnmix() or
        from rmag.backfield_unmixing()

    updates the specimen table in place
    '''
    if method == 'lmfit':
        unmix_result_dict = unmix_result.params.valuesdict()
    elif method == 'MaxUnmix':
        unmix_result_dict = unmix_result
    else:
        raise ValueError(f"method should be either 'lmfit' or 'MaxUnmix', but got {method}")
    unmix_result_dict = dict_in_native_python(unmix_result_dict)
    # merge into the description cell, preserving free text and any
    # existing structured content (parsed safely rather than with eval)
    mask = specimens_df['experiments'] == experiment_name
    for idx in specimens_df.index[mask]:
        text, description_dict = parse_specimen_description(
            specimens_df.at[idx, 'description'])
        description_dict.update(unmix_result_dict)
        payload = json.dumps(description_dict)
        specimens_df.at[idx, 'description'] = (
            f'{text} | {payload}' if text else payload)
    return

def add_Bcr_to_specimens_table(specimens_df, experiment_name, Bcr):
    """
    Add the Bcr value to the MagIC specimens table
    the controled vocabulary for backfield derived Bcr is rem_bcr

    Parameters
    ----------
    specimens_df : pandas.DataFrame
        The specimens table from the MagIC database
    experiment_name : str
        The name of the experiment to which the Bcr value belongs
    Bcr : float
        The Bcr value to be added to the specimens table
    """
    # first check if the rem_bcr column exists
    if 'rem_bcr' not in specimens_df.columns:
        # add the rem_bcr column to the specimens table
        specimens_df['rem_bcr'] = np.nan
    # add the Bcr value to the specimens table
    specimens_df.loc[specimens_df['experiments'] == experiment_name, 'rem_bcr'] = Bcr

    return


# coercivity spectrum unmixing functions
# ------------------------------------------------------------------------------------------------------------------
# Toolkit for decomposing remanence curves (backfield demagnetization or IRM
# acquisition) into coercivity components. Every component is a skew-normal
# distribution in x = log10(B/mT) parameterized by its integrated area
# ('contribution', in the units of the magnetization data), location, scale
# ('dp'), and shape ('skew'). With skew = 0 the component reduces exactly to
# the log-Gaussian of Robertson & France (1994). Because the skew-normal has
# an analytic CDF (via Owen's T function), the same component model can be
# fit in two data spaces:
#
#   1. spectrum space -- fitting the coercivity spectrum |dM/dlog10(B)|,
#      following Kruiver et al. (2001), Egli (2003), and the MAX UnMix
#      program of Maxbauer et al. (2016).
#   2. measurement space -- fitting the measured remanence curve M(B)
#      directly with cumulative (CDF) components, which avoids numerical
#      differentiation and smoothing of the data altogether.
#
# Model selection is supported through AIC/BIC and F-tests, and parameter
# uncertainties through both linearized (covariance) standard errors and
# bootstrap resampling.

_SQRT2 = np.sqrt(2.0)
_SQRT2PI = np.sqrt(2.0 * np.pi)
UNMIX_PARAM_COLUMNS = ['contribution', 'location', 'dp', 'skew']


def _trapz(y, x):
    """Trapezoidal integration compatible with numpy 1.x and 2.x."""
    trapezoid = getattr(np, 'trapezoid', None)
    if trapezoid is None:
        trapezoid = np.trapz
    return trapezoid(y, x)


def skewnormal_pdf(x, location, dp, skew=0.0):
    """
    Skew-normal probability density function (unit area).

    With skew = 0 this is a Gaussian with mean = location and standard
    deviation = dp; in log10(B) coordinates that Gaussian is the log-Gaussian
    coercivity distribution of Robertson & France (1994). Nonzero skew
    follows the Azzalini (1985) formulation: negative values skew the
    distribution toward low values (tail to the left).

    Parameters
    ----------
    x : array-like
        Points at which to evaluate the density (log10 of field in mT).
    location : float
        Location parameter (log10 mT). Equal to the mean only when skew = 0.
    dp : float
        Scale parameter (log10 units); must be positive. Equal to the
        standard deviation only when skew = 0.
    skew : float
        Shape parameter alpha of the Azzalini skew-normal (default 0).

    Returns
    -------
    numpy.ndarray
        Density values with unit integrated area.
    """
    x = np.asarray(x, dtype=float)
    z = (x - location) / dp
    return np.exp(-0.5 * z * z) / (_SQRT2PI * dp) * (1.0 + erf(skew * z / _SQRT2))


def skewnormal_cdf(x, location, dp, skew=0.0):
    """
    Skew-normal cumulative distribution function.

    Evaluated analytically as Phi(z) - 2*T(z, skew) where T is Owen's T
    function (scipy.special.owens_t).

    Parameters
    ----------
    x : array-like
        Points at which to evaluate the CDF (log10 of field in mT).
    location : float
        Location parameter (log10 mT).
    dp : float
        Scale parameter (log10 units); must be positive.
    skew : float
        Shape parameter alpha (default 0).

    Returns
    -------
    numpy.ndarray
        CDF values between 0 and 1.
    """
    x = np.asarray(x, dtype=float)
    z = (x - location) / dp
    Phi = 0.5 * (1.0 + erf(z / _SQRT2))
    if skew == 0:
        return Phi
    return Phi - 2.0 * owens_t(z, skew)


def skewnormal_stats(location, dp, skew=0.0):
    """
    Moments and characteristic points of a skew-normal distribution.

    Parameters
    ----------
    location : float
        Location parameter (log10 mT).
    dp : float
        Scale parameter (log10 units).
    skew : float
        Shape parameter alpha.

    Returns
    -------
    dict
        With keys 'mean', 'std', 'median', and 'mode', all in the same
        (log10) units as location and dp. For skew = 0 all of mean, median,
        and mode equal location and std equals dp.
    """
    delta = skew / np.sqrt(1.0 + skew ** 2)
    mean = location + dp * delta * np.sqrt(2.0 / np.pi)
    std = dp * np.sqrt(1.0 - 2.0 * delta ** 2 / np.pi)
    if skew == 0:
        return {'mean': mean, 'std': std, 'median': location, 'mode': location}
    median = brentq(lambda t: skewnormal_cdf(t, location, dp, skew) - 0.5,
                    location - 12 * dp, location + 12 * dp)
    mode_res = minimize_scalar(lambda t: -skewnormal_pdf(t, location, dp, skew),
                               bounds=(location - 5 * dp, location + 5 * dp),
                               method='bounded')
    return {'mean': mean, 'std': std, 'median': median, 'mode': float(mode_res.x)}


def _unmix_parameters_to_array(parameters):
    """Coerce a parameters DataFrame/array to an (n_components, 4) float array."""
    if isinstance(parameters, pd.DataFrame):
        missing = [c for c in UNMIX_PARAM_COLUMNS if c not in parameters.columns]
        if missing:
            raise KeyError(f"parameters table is missing columns: {missing}")
        return parameters[UNMIX_PARAM_COLUMNS].to_numpy(dtype=float)
    arr = np.atleast_2d(np.asarray(parameters, dtype=float))
    if arr.shape[1] != 4:
        raise ValueError("parameters must have four columns: "
                         f"{UNMIX_PARAM_COLUMNS}")
    return arr


def coercivity_spectrum_components(x, parameters):
    """
    Evaluate each unmixing component in spectrum space (dM/dlog10 B).

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    parameters : pandas.DataFrame or array-like
        One row per component with columns 'contribution' (area under the
        component in magnetization units), 'location', 'dp', 'skew'.

    Returns
    -------
    numpy.ndarray
        Array of shape (n_components, len(x)).
    """
    arr = _unmix_parameters_to_array(parameters)
    x = np.asarray(x, dtype=float)
    return np.array([c * skewnormal_pdf(x, loc, dp, skew)
                     for c, loc, dp, skew in arr])


def coercivity_spectrum_model(x, parameters):
    """
    Evaluate the summed unmixing model in spectrum space.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    parameters : pandas.DataFrame or array-like
        Component parameters (see coercivity_spectrum_components).

    Returns
    -------
    numpy.ndarray
        Total model spectrum at x.
    """
    return coercivity_spectrum_components(x, parameters).sum(axis=0)


def coercivity_curve_components(x, parameters, curve_type='backfield'):
    """
    Evaluate each component in measurement space (cumulative curves).

    For 'backfield' curves (processed so that magnetization decays from a
    maximum toward zero with increasing field magnitude) each component is
    contribution * (1 - CDF); for 'acquisition' curves each component is
    contribution * CDF.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    parameters : pandas.DataFrame or array-like
        Component parameters (see coercivity_spectrum_components).
    curve_type : str
        'backfield' or 'acquisition'.

    Returns
    -------
    numpy.ndarray
        Array of shape (n_components, len(x)).
    """
    assert curve_type in ('backfield', 'acquisition'), \
        "curve_type must be 'backfield' or 'acquisition'"
    arr = _unmix_parameters_to_array(parameters)
    x = np.asarray(x, dtype=float)
    comps = []
    for c, loc, dp, skew in arr:
        cdf = skewnormal_cdf(x, loc, dp, skew)
        comps.append(c * (1.0 - cdf) if curve_type == 'backfield' else c * cdf)
    return np.array(comps)


def coercivity_curve_model(x, parameters, offset=0.0, curve_type='backfield'):
    """
    Evaluate the summed unmixing model in measurement space.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    parameters : pandas.DataFrame or array-like
        Component parameters (see coercivity_spectrum_components).
    offset : float
        Constant baseline added to the model (accounts for a small
        unsaturated or instrumental offset; default 0).
    curve_type : str
        'backfield' or 'acquisition'.

    Returns
    -------
    numpy.ndarray
        Total model curve at x.
    """
    return coercivity_curve_components(x, parameters, curve_type).sum(axis=0) + offset


def coercivity_spectrum_from_curve(x, magnetization, curve_type='backfield'):
    """
    Compute a finite-difference coercivity spectrum from a remanence curve.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT), monotonically increasing.
    magnetization : array-like
        Magnetization values at x (shifted to positive for backfield data,
        e.g. the 'magn_mass_shift' column from backfield_data_processing).
    curve_type : str
        'backfield' (decaying curve, spectrum = -dM/dx) or 'acquisition'
        (growing curve, spectrum = dM/dx).

    Returns
    -------
    tuple
        (x_mid, spectrum) where x_mid are midpoints between successive x
        values and spectrum is the centered finite-difference derivative.
    """
    assert curve_type in ('backfield', 'acquisition'), \
        "curve_type must be 'backfield' or 'acquisition'"
    x = np.asarray(x, dtype=float)
    M = np.asarray(magnetization, dtype=float)
    dM = np.diff(M) / np.diff(x)
    x_mid = 0.5 * (x[1:] + x[:-1])
    return x_mid, (-dM if curve_type == 'backfield' else dM)


def estimate_coercivity_components(x, spectrum, n_components, smooth_window=None):
    """
    Automatic initial-guess estimation for unmixing components.

    The spectrum is interpolated onto a uniform grid, lightly smoothed
    (Savitzky-Golay), and searched for peaks. The n_components most
    prominent peaks seed the component locations; widths at half maximum
    seed dp; peak heights seed the contributions. If fewer peaks than
    components are found, the remaining components are placed at evenly
    spaced quantiles of the cumulative spectrum.

    Initial choices matter for nonlinear fitting: these automatic estimates
    are a starting point that can (and often should) be refined by the user,
    e.g. with interactive_coercivity_unmixing.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    spectrum : array-like
        Coercivity spectrum values at x.
    n_components : int
        Number of components to estimate.
    smooth_window : int, optional
        Savitzky-Golay window length (grid points). Defaults to ~1/10 of
        the grid (minimum 5).

    Returns
    -------
    pandas.DataFrame
        Initial parameters with columns 'contribution', 'location', 'dp',
        'skew' (skew = 0), sorted by location.
    """
    assert isinstance(n_components, (int, np.integer)) and n_components > 0, \
        'n_components must be a positive integer'
    x = np.asarray(x, dtype=float)
    y = np.asarray(spectrum, dtype=float)
    order = np.argsort(x)
    x, y = x[order], y[order]

    n_grid = max(200, len(x))
    xg = np.linspace(x.min(), x.max(), n_grid)
    yg = np.interp(xg, x, y)
    if smooth_window is None:
        smooth_window = max(5, (n_grid // 10) | 1)  # odd
    else:
        smooth_window = max(5, int(smooth_window) | 1)
    yg_smooth = savgol_filter(yg, smooth_window, polyorder=3)
    yg_smooth = np.clip(yg_smooth, 0, None)
    dx = xg[1] - xg[0]

    peak_idx, props = find_peaks(yg_smooth, prominence=0.02 * yg_smooth.max(),
                                 width=1)
    if len(peak_idx) > 0:
        # keep the n most prominent peaks
        keep = np.argsort(props['prominences'])[::-1][:n_components]
        peak_idx = peak_idx[keep]
        widths = props['widths'][keep] * dx
    else:
        peak_idx = np.array([], dtype=int)
        widths = np.array([])

    locations = list(xg[peak_idx])
    dps = [max(w / 2.355, 0.05) for w in widths]  # FWHM -> sigma
    heights = list(yg_smooth[peak_idx])

    # fill any missing components at quantiles of the cumulative spectrum
    if len(locations) < n_components:
        cumulative = np.cumsum(yg_smooth)
        cumulative = cumulative / cumulative[-1]
        n_missing = n_components - len(locations)
        quantiles = np.linspace(0.15, 0.85, n_components)
        candidates = [xg[np.searchsorted(cumulative, q)] for q in quantiles]
        # prefer candidate positions away from already-found peaks
        for cand in sorted(candidates,
                           key=lambda c: -min([abs(c - loc) for loc in locations],
                                              default=np.inf)):
            if n_missing == 0:
                break
            locations.append(cand)
            dps.append(0.25)
            heights.append(np.interp(cand, xg, yg_smooth))
            n_missing -= 1

    initial = pd.DataFrame({
        'contribution': [h * dp * _SQRT2PI for h, dp in zip(heights, dps)],
        'location': locations,
        'dp': dps,
        'skew': 0.0,
    })
    return initial.sort_values('location').reset_index(drop=True)


def _unmix_fit_engine(x, y, initial, method, curve_type='backfield',
                      vary_skew=True, fit_offset=True, weights=None,
                      dp_bounds=(0.01, 2.0), skew_bounds=(-10.0, 10.0),
                      max_nfev=20000):
    """
    Shared bounded least-squares engine for both unmixing data spaces.

    Returns the scipy result plus unpacked, physically scaled parameter
    arrays, standard errors, and offset. Used by unmix_coercivity_spectrum
    and unmix_backfield_curve; not intended to be called directly.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    assert len(x) == len(y), 'x and y must have the same length'
    finite = np.isfinite(x) & np.isfinite(y)
    x, y = x[finite], y[finite]
    if weights is not None:
        weights = np.asarray(weights, dtype=float)[finite]

    init_arr = _unmix_parameters_to_array(initial)
    K = init_arr.shape[0]
    if len(x) <= 3 * K + 1:
        raise ValueError(f'too few data points ({len(x)}) to fit '
                         f'{K} components')

    y_scale = np.max(np.abs(y))
    if y_scale == 0:
        raise ValueError('y data are all zero')
    ys = y / y_scale

    c0 = np.clip(init_arr[:, 0] / y_scale, 1e-6, 20.0)
    loc0 = np.clip(init_arr[:, 1], x.min() - 0.5, x.max() + 0.5)
    dp0 = np.clip(init_arr[:, 2], dp_bounds[0], dp_bounds[1])
    skew0 = np.clip(init_arr[:, 3], skew_bounds[0], skew_bounds[1])

    fit_offset = fit_offset and method == 'curve'
    p0 = np.concatenate([c0, loc0, dp0])
    lb = np.concatenate([np.zeros(K), np.full(K, x.min() - 0.5),
                         np.full(K, dp_bounds[0])])
    ub = np.concatenate([np.full(K, 20.0), np.full(K, x.max() + 0.5),
                         np.full(K, dp_bounds[1])])
    if vary_skew:
        p0 = np.concatenate([p0, skew0])
        lb = np.concatenate([lb, np.full(K, skew_bounds[0])])
        ub = np.concatenate([ub, np.full(K, skew_bounds[1])])
    if fit_offset:
        p0 = np.concatenate([p0, [0.0]])
        lb = np.concatenate([lb, [-0.5]])
        ub = np.concatenate([ub, [0.5]])

    def unpack(p):
        c = p[:K]
        loc = p[K:2 * K]
        dp = p[2 * K:3 * K]
        skew = p[3 * K:4 * K] if vary_skew else skew0
        offset = p[-1] if fit_offset else 0.0
        return c, loc, dp, skew, offset

    def model_scaled(p):
        c, loc, dp, skew, offset = unpack(p)
        params = np.column_stack([c, loc, dp, skew])
        if method == 'spectrum':
            return coercivity_spectrum_model(x, params)
        return coercivity_curve_model(x, params, offset=offset,
                                      curve_type=curve_type)

    def residuals(p):
        r = model_scaled(p) - ys
        return r * weights if weights is not None else r

    res = least_squares(residuals, p0, bounds=(lb, ub), method='trf',
                        x_scale='jac', max_nfev=max_nfev)

    # covariance-based standard errors (linearized approximation)
    n_pts, n_par = len(x), len(res.x)
    dof = n_pts - n_par
    se = np.full(n_par, np.nan)
    if dof > 0:
        try:
            JtJ = res.jac.T @ res.jac
            cov = 2.0 * res.cost / dof * np.linalg.pinv(JtJ)
            se = np.sqrt(np.clip(np.diag(cov), 0, None))
        except np.linalg.LinAlgError:
            pass

    c, loc, dp, skew, offset = unpack(res.x)
    se_c = se[:K] * y_scale
    se_loc = se[K:2 * K]
    se_dp = se[2 * K:3 * K]
    se_skew = se[3 * K:4 * K] if vary_skew else np.zeros(K)
    se_offset = se[-1] * y_scale if fit_offset else 0.0

    # order components by mean coercivity
    delta = skew / np.sqrt(1.0 + skew ** 2)
    means = loc + dp * delta * np.sqrt(2.0 / np.pi)
    order = np.argsort(means)

    return {
        'scipy_result': res,
        'contribution': c[order] * y_scale, 'se_contribution': se_c[order],
        'location': loc[order], 'se_location': se_loc[order],
        'dp': dp[order], 'se_dp': se_dp[order],
        'skew': np.asarray(skew)[order], 'se_skew': np.asarray(se_skew)[order],
        'offset': offset * y_scale, 'se_offset': se_offset,
        'x': x, 'y': y, 'weights': weights, 'y_scale': y_scale,
    }


def _build_unmix_result(engine, method, curve_type, vary_skew, fit_offset,
                        initial):
    """Assemble the standardized result dictionary from the fit engine output."""
    K = len(engine['contribution'])
    rows = []
    for i in range(K):
        stats_i = skewnormal_stats(engine['location'][i], engine['dp'][i],
                                   engine['skew'][i])
        rows.append({
            'contribution': engine['contribution'][i],
            'se_contribution': engine['se_contribution'][i],
            'location': engine['location'][i],
            'se_location': engine['se_location'][i],
            'dp': engine['dp'][i],
            'se_dp': engine['se_dp'][i],
            'skew': engine['skew'][i],
            'se_skew': engine['se_skew'][i],
            'sd_log': stats_i['std'],
            'log10_B_mean': stats_i['mean'],
            'B_mean_mT': 10 ** stats_i['mean'],
            'B_median_mT': 10 ** stats_i['median'],
            'B_peak_mT': 10 ** stats_i['mode'],
        })
    params = pd.DataFrame(rows, index=pd.RangeIndex(1, K + 1,
                                                    name='component'))
    total = params['contribution'].sum()
    params.insert(1, 'proportion',
                  params['contribution'] / total if total > 0 else np.nan)

    x, y = engine['x'], engine['y']
    param_arr = params[UNMIX_PARAM_COLUMNS].to_numpy()
    if method == 'spectrum':
        y_fit = coercivity_spectrum_model(x, param_arr)
    else:
        y_fit = coercivity_curve_model(x, param_arr, offset=engine['offset'],
                                       curve_type=curve_type)
    residuals = y - y_fit
    n = len(x)
    n_params = (3 + int(vary_skew)) * K + int(fit_offset and method == 'curve')
    rss = float(np.sum(residuals ** 2))
    tss = float(np.sum((y - y.mean()) ** 2))
    dof = n - n_params
    # Gaussian-likelihood information criteria (constant terms omitted);
    # comparable only between fits to the same data
    with np.errstate(divide='ignore'):
        log_term = np.log(rss / n) if rss > 0 else -np.inf
    stats = {
        'n': n,
        'n_params': n_params,
        'dof': dof,
        'rss': rss,
        'r_squared': 1.0 - rss / tss if tss > 0 else np.nan,
        'reduced_chi_square': rss / dof if dof > 0 else np.nan,
        'aic': n * log_term + 2 * n_params,
        'bic': n * log_term + n_params * np.log(n),
    }

    scipy_result = engine['scipy_result']
    initial_df = (initial.copy() if isinstance(initial, pd.DataFrame)
                  else pd.DataFrame(_unmix_parameters_to_array(initial),
                                    columns=UNMIX_PARAM_COLUMNS))
    return {
        'method': method,
        'curve_type': curve_type,
        'n_components': K,
        'success': bool(scipy_result.success),
        'message': scipy_result.message,
        'params': params,
        'offset': engine['offset'],
        'se_offset': engine['se_offset'],
        'x': x,
        'y': y,
        'y_fit': y_fit,
        'residuals': residuals,
        'weights': engine['weights'],
        'stats': stats,
        'initial_parameters': initial_df,
        'vary_skew': vary_skew,
    }


def unmix_coercivity_spectrum(x, spectrum, n_components=None,
                              initial_parameters=None, vary_skew=True,
                              weights=None, dp_bounds=(0.01, 2.0),
                              skew_bounds=(-10.0, 10.0)):
    """
    Unmix a coercivity spectrum into skew-normal (log-Gaussian) components.

    Fits the derivative spectrum dM/dlog10(B) with a sum of skew-normal
    densities, following the approach popularized by Kruiver et al. (2001)
    and the MAX UnMix program (Maxbauer et al., 2016). Compared to fitting
    the measured curve directly (unmix_backfield_curve) this operates on a
    numerically differentiated (and possibly smoothed) version of the data,
    so the choice of smoothing can influence the result; the advantage is
    that components are fit in the space where they are most readily
    interpreted visually.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT), e.g. midpoints from
        coercivity_spectrum_from_curve.
    spectrum : array-like
        Coercivity spectrum values at x (magnetization per decade).
    n_components : int, optional
        Number of components. Required if initial_parameters is None.
    initial_parameters : pandas.DataFrame, optional
        Initial guesses with columns 'contribution', 'location', 'dp',
        'skew' (one row per component). If None, automatic estimates from
        estimate_coercivity_components are used.
    vary_skew : bool
        If False, skew values are fixed at their initial values (default 0,
        i.e. symmetric log-Gaussian components).
    weights : array-like, optional
        Multiplicative weights applied to the residuals.
    dp_bounds : tuple
        (min, max) bounds on the dp scale parameter in log10 units.
    skew_bounds : tuple
        (min, max) bounds on the skew shape parameter.

    Returns
    -------
    dict
        Standardized result dictionary with keys including 'params' (a
        DataFrame of fitted parameters, linearized standard errors, and
        derived quantities such as B_mean_mT and proportion), 'y_fit',
        'residuals', 'stats' (rss, r_squared, aic, bic, ...), 'success',
        and 'initial_parameters'.
    """
    if initial_parameters is None:
        if n_components is None:
            raise ValueError('specify n_components or initial_parameters')
        initial_parameters = estimate_coercivity_components(x, spectrum,
                                                            n_components)
    elif (n_components is not None
          and len(initial_parameters) != n_components):
        raise ValueError('n_components does not match the number of rows in '
                         'initial_parameters')
    engine = _unmix_fit_engine(x, spectrum, initial_parameters,
                               method='spectrum', vary_skew=vary_skew,
                               weights=weights, dp_bounds=dp_bounds,
                               skew_bounds=skew_bounds)
    return _build_unmix_result(engine, 'spectrum', 'backfield', vary_skew,
                               False, initial_parameters)


def unmix_backfield_curve(x, magnetization, n_components=None,
                          initial_parameters=None, curve_type='backfield',
                          vary_skew=True, fit_offset=True, weights=None,
                          dp_bounds=(0.01, 2.0), skew_bounds=(-10.0, 10.0)):
    """
    Unmix a remanence curve by fitting cumulative components directly.

    Fits the measured curve M(log10 B) with a sum of skew-normal CDF
    components (plus an optional constant offset), avoiding numerical
    differentiation and smoothing entirely. The component parameterization
    is identical to unmix_coercivity_spectrum, so results from the two
    data spaces are directly comparable. Fitting in measurement space uses
    the raw measurements with their original noise structure; fitting in
    spectrum space can be more visually intuitive. Agreement between the
    two approaches is a good indication of a robust unmixing model.

    For backfield data processed with backfield_data_processing, pass
    x = 'log_dc_field' and magnetization = 'magn_mass_shift'. Note that the
    shifted backfield curve spans twice the saturation remanence, so each
    fitted 'contribution' is twice the remanence carried by that component;
    'proportion' values are unaffected.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    magnetization : array-like
        Remanence curve values at x (shifted positive for backfield data).
    n_components : int, optional
        Number of components. Required if initial_parameters is None.
    initial_parameters : pandas.DataFrame, optional
        Initial guesses (see unmix_coercivity_spectrum). If None, automatic
        estimates are derived from the finite-difference spectrum.
    curve_type : str
        'backfield' (decaying curve) or 'acquisition' (growing curve).
    vary_skew : bool
        If False, skew values are fixed at their initial values.
    fit_offset : bool
        Whether to fit a constant baseline offset (default True).
    weights : array-like, optional
        Multiplicative weights applied to the residuals.
    dp_bounds, skew_bounds : tuple
        Bounds as in unmix_coercivity_spectrum.

    Returns
    -------
    dict
        Standardized result dictionary (see unmix_coercivity_spectrum),
        additionally including the fitted 'offset' and 'se_offset'.
    """
    if initial_parameters is None:
        if n_components is None:
            raise ValueError('specify n_components or initial_parameters')
        x_mid, spec = coercivity_spectrum_from_curve(x, magnetization,
                                                     curve_type)
        initial_parameters = estimate_coercivity_components(x_mid, spec,
                                                            n_components)
    elif (n_components is not None
          and len(initial_parameters) != n_components):
        raise ValueError('n_components does not match the number of rows in '
                         'initial_parameters')
    engine = _unmix_fit_engine(x, magnetization, initial_parameters,
                               method='curve', curve_type=curve_type,
                               vary_skew=vary_skew, fit_offset=fit_offset,
                               weights=weights, dp_bounds=dp_bounds,
                               skew_bounds=skew_bounds)
    return _build_unmix_result(engine, 'curve', curve_type, vary_skew,
                               fit_offset, initial_parameters)


def _unmix_method_spectrum(x, magnetization, n_components=None,
                           initial_parameters=None, curve_type='backfield',
                           vary_skew=True, **kwargs):
    """Registered 'spectrum' method: finite-difference spectrum fit."""
    x_mid, spectrum = coercivity_spectrum_from_curve(x, magnetization,
                                                     curve_type)
    return unmix_coercivity_spectrum(x_mid, spectrum,
                                     n_components=n_components,
                                     initial_parameters=initial_parameters,
                                     vary_skew=vary_skew, **kwargs)


def _unmix_method_curve(x, magnetization, n_components=None,
                        initial_parameters=None, curve_type='backfield',
                        vary_skew=True, **kwargs):
    """Registered 'curve' method: direct measurement-space fit."""
    return unmix_backfield_curve(x, magnetization, n_components=n_components,
                                 initial_parameters=initial_parameters,
                                 curve_type=curve_type, vary_skew=vary_skew,
                                 **kwargs)


def _unmix_method_maxunmix(x, magnetization, n_components=None,
                           initial_parameters=None, curve_type='backfield',
                           vary_skew=True, n_boot=100, proportion=0.95,
                           param_noise=0.02, random_seed=None, n_grid=200,
                           **kwargs):
    """
    Registered 'maxunmix' method: a faithful reproduction of the MAX UnMix
    resampling workflow (Maxbauer et al., 2016), for direct comparison with
    that program.

    The coercivity spectrum dM/dlog10(B) is fit with skew-normal components,
    and uncertainties are estimated exactly as in MAX UnMix: each of `n_boot`
    replicates (1) recomputes the spectrum from a random `proportion`
    (default 0.95) subset of the magnetization points drawn WITHOUT
    replacement, (2) restarts the fit from the best-fit parameters perturbed
    by `param_noise` (default 0.02, i.e. 2%) Gaussian noise, and (3)
    re-optimizes; percentile intervals over the converged replicates are
    reported (attached as the 'bootstrap' entry of the result).

    Two representational differences from MAX UnMix remain because they are
    intrinsic to the rockmagpy component model rather than to the resampling:
    skewness follows the Azzalini rather than the Fernandez-Steel (fGarch)
    parameterization, so skew values are not numerically comparable, and
    components are parameterized by integrated area rather than by peak
    height. Recovered coercivities, dispersions, and relative contributions
    are directly comparable to the MAX UnMix web application.

    For the more flexible rockmagpy resampling -- case or residual resampling
    of the fitted data, optionally with added measurement noise, and usable
    with the measurement-space and Bayesian fits as well -- fit with
    method='spectrum' or 'curve' and call unmixing_bootstrap directly.
    """
    rng = _resolve_rng(random_seed)
    x = np.asarray(x, dtype=float)
    M = np.asarray(magnetization, dtype=float)
    finite = np.isfinite(x) & np.isfinite(M)
    x, M = x[finite], M[finite]

    x_mid, spectrum = coercivity_spectrum_from_curve(x, M, curve_type)
    result = unmix_coercivity_spectrum(x_mid, spectrum,
                                       n_components=n_components,
                                       initial_parameters=initial_parameters,
                                       vary_skew=vary_skew, **kwargs)
    best = result['params'][UNMIX_PARAM_COLUMNS].to_numpy()
    K = result['n_components']
    n = len(x)
    n_keep = max(int(round(n * proportion)), 3 * K + 3)

    # forward the same fit settings (e.g. dp_bounds, skew_bounds) to every
    # replicate so it runs under the identical constraints as the main fit.
    # 'weights' is excluded: each replicate recomputes the spectrum from a
    # random subset of the curve, so per-point weights of the full spectrum
    # cannot align with the shorter resampled spectrum.
    replicate_kwargs = {k: v for k, v in kwargs.items() if k != 'weights'}

    tracked = ['contribution', 'proportion', 'location', 'dp', 'skew',
               'sd_log', 'B_mean_mT', 'B_median_mT', 'B_peak_mT']
    samples = {name: [] for name in tracked}
    x_grid = np.linspace(x_mid.min(), x_mid.max(), n_grid)
    total_curves, comp_curves = [], []
    n_success = 0
    for _ in range(n_boot):
        # (1) recompute the spectrum from a 95% subset of the curve, w/o replacement
        idx = np.sort(rng.choice(n, size=n_keep, replace=False))
        x_mid_b, spectrum_b = coercivity_spectrum_from_curve(x[idx], M[idx],
                                                             curve_type)
        # (2) restart from the best fit perturbed by ~2% Gaussian noise
        init = best.copy()
        init[:, 0] *= 1.0 + rng.normal(0.0, param_noise, K)   # contribution
        init[:, 1] *= 1.0 + rng.normal(0.0, param_noise, K)   # location
        init[:, 2] *= 1.0 + rng.normal(0.0, param_noise, K)   # dispersion
        if vary_skew:
            init[:, 3] += rng.normal(0.0, 5.0 * param_noise, K)  # skew jitter
        init[:, 0] = np.abs(init[:, 0])
        try:
            fit = unmix_coercivity_spectrum(
                x_mid_b, spectrum_b, vary_skew=vary_skew,
                initial_parameters=pd.DataFrame(init,
                                                columns=UNMIX_PARAM_COLUMNS),
                **replicate_kwargs)
        except (ValueError, RuntimeError):
            continue
        if not fit['success']:
            continue
        p = fit['params']
        for name in tracked:
            samples[name].append(p[name].to_numpy())
        arr = p[UNMIX_PARAM_COLUMNS].to_numpy()
        total_curves.append(coercivity_spectrum_model(x_grid, arr))
        comp_curves.append(coercivity_spectrum_components(x_grid, arr))
        n_success += 1

    if n_success < max(10, n_boot // 10):
        raise RuntimeError(f'only {n_success} of {n_boot} MAX UnMix '
                           'replicates converged; check the fit or initial '
                           'parameters')

    percentiles = [2.5, 50, 97.5]
    summary_rows = []
    for comp in range(K):
        row = {'component': comp + 1}
        for name in tracked:
            vals = np.array([s[comp] for s in samples[name]])
            row[f'{name}_mean'] = vals.mean()
            row[f'{name}_std'] = vals.std()
            for pct in percentiles:
                row[f'{name}_p{str(pct).replace(".", "_")}'] = \
                    np.percentile(vals, pct)
        summary_rows.append(row)
    param_summary = pd.DataFrame(summary_rows).set_index('component')

    total_curves = np.array(total_curves)
    comp_curves = np.array(comp_curves)
    curves = {
        'x_grid': x_grid,
        'total_p2_5': np.percentile(total_curves, 2.5, axis=0),
        'total_p50': np.percentile(total_curves, 50, axis=0),
        'total_p97_5': np.percentile(total_curves, 97.5, axis=0),
        'components_p2_5': np.percentile(comp_curves, 2.5, axis=0),
        'components_p50': np.percentile(comp_curves, 50, axis=0),
        'components_p97_5': np.percentile(comp_curves, 97.5, axis=0),
    }
    result['bootstrap'] = {
        'method': 'maxunmix',
        'n_boot': n_boot,
        'n_success': n_success,
        'resample': 'maxunmix: 95% subsample without replacement '
                    '+ 2% restart-parameter perturbation',
        'proportion': proportion,
        'param_noise': param_noise,
        'param_summary': param_summary,
        'param_samples': {name: np.array(vals)
                          for name, vals in samples.items()},
        'curves': curves,
    }
    return result


UNMIXING_METHODS = {
    'spectrum': _unmix_method_spectrum,
    'curve': _unmix_method_curve,
    'maxunmix': _unmix_method_maxunmix,
}


def register_unmixing_method(name, function):
    """
    Register a custom coercivity unmixing method.

    Registered methods become available through unmix_coercivity and
    unmix_backfield_experiments alongside the built-in 'spectrum', 'curve',
    and 'maxunmix' methods. The function must accept
    (x, magnetization, n_components=None, initial_parameters=None,
    curve_type='backfield', vary_skew=True, **kwargs) and return the
    standardized result dictionary (see unmix_coercivity_spectrum); the
    component model helpers (skewnormal_pdf, coercivity_spectrum_model,
    coercivity_curve_model, ...) can be reused when implementing new
    methods.

    Parameters
    ----------
    name : str
        Name under which the method is registered.
    function : callable
        The method implementation.

    Returns
    -------
    None
    """
    if not callable(function):
        raise TypeError('function must be callable')
    UNMIXING_METHODS[name] = function


def unmix_coercivity(x, magnetization, method='spectrum', n_components=None,
                     initial_parameters=None, curve_type='backfield',
                     vary_skew=True, **kwargs):
    """
    Unmix a remanence curve into coercivity components with a named method.

    This is the common entry point to the unmixing approaches implemented
    in rockmagpy (and to any user-registered methods; see
    register_unmixing_method). All methods take the measured remanence
    curve -- not a precomputed derivative -- and share the same skew-normal
    component parameterization, so their results are directly comparable.

    Built-in methods:

    - 'spectrum': fits the finite-difference coercivity spectrum
      dM/dlog10(B) with skew-normal components (Kruiver et al., 2001;
      Egli, 2003 lineage). Point estimates only; combine with
      unmixing_bootstrap for uncertainties.
    - 'curve': fits the measured curve directly with cumulative
      (CDF) components, avoiding numerical differentiation entirely.
    - 'maxunmix': the 'spectrum' fit plus the MAX UnMix resampling
      uncertainty scheme (Maxbauer et al., 2016): 95% case resampling with
      2% noise, 100 replicates by default.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT), e.g. 'log_dc_field' from
        backfield_data_processing.
    magnetization : array-like
        Remanence curve values at x (e.g. 'magn_mass_shift').
    method : str
        Name of a registered unmixing method (default 'spectrum').
    n_components : int, optional
        Number of components (required if initial_parameters is None).
    initial_parameters : pandas.DataFrame, optional
        Initial guesses with columns 'contribution', 'location', 'dp',
        'skew'; automatic estimates are used when omitted.
    curve_type : str
        'backfield' or 'acquisition'.
    vary_skew : bool
        Whether skew parameters vary during fitting.
    **kwargs
        Passed through to the method implementation (e.g. n_boot,
        proportion, param_noise for 'maxunmix'; fit_offset for 'curve';
        dp_bounds, skew_bounds for the spectrum-based methods).

    Returns
    -------
    dict
        Standardized result dictionary (see unmix_coercivity_spectrum).
    """
    if method not in UNMIXING_METHODS:
        raise ValueError(f"unknown unmixing method '{method}'; available: "
                         f'{sorted(UNMIXING_METHODS)}')
    return UNMIXING_METHODS[method](x, magnetization,
                                    n_components=n_components,
                                    initial_parameters=initial_parameters,
                                    curve_type=curve_type,
                                    vary_skew=vary_skew, **kwargs)


def compare_unmixing_models(results):
    """
    Compare unmixing fits with different numbers of components.

    Builds a comparison table with information criteria and sequential
    F-tests. All results must be fits of the same data with the same
    method ('spectrum' or 'curve'); AIC/BIC values are only meaningful
    relative to one another under that condition. The F-test compares each
    model to the previous (simpler) one; a small p-value indicates the
    additional component produces a statistically significant improvement.
    As emphasized by Maxbauer et al. (2016) and Egli (2003), statistical
    significance alone should not decide the number of components --
    independent knowledge of the likely magnetic mineralogy should inform
    the choice.

    Parameters
    ----------
    results : list of dict
        Result dictionaries from unmix_coercivity_spectrum or
        unmix_backfield_curve, typically with increasing n_components.

    Returns
    -------
    pandas.DataFrame
        One row per model with n_components, n_params, rss, r_squared,
        aic, bic, delta_aic, delta_bic, F, and p_value columns.
    """
    from scipy.stats import f as f_distribution
    if len(results) == 0:
        raise ValueError('results list is empty')
    methods = {r['method'] for r in results}
    lengths = {len(r['x']) for r in results}
    if len(methods) > 1 or len(lengths) > 1:
        raise ValueError('all results must fit the same data with the same '
                         'method for a meaningful comparison')
    ordered = sorted(results, key=lambda r: r['stats']['n_params'])
    rows = []
    for i, r in enumerate(ordered):
        s = r['stats']
        row = {
            'n_components': r['n_components'],
            'n_params': s['n_params'],
            'rss': s['rss'],
            'r_squared': s['r_squared'],
            'aic': s['aic'],
            'bic': s['bic'],
            'F': np.nan,
            'p_value': np.nan,
        }
        if i > 0:
            s0 = ordered[i - 1]['stats']
            dp_extra = s['n_params'] - s0['n_params']
            if dp_extra > 0 and s['dof'] > 0 and s['rss'] > 0:
                F = ((s0['rss'] - s['rss']) / dp_extra) / (s['rss'] / s['dof'])
                row['F'] = F
                row['p_value'] = float(f_distribution.sf(F, dp_extra,
                                                         s['dof']))
        rows.append(row)
    table = pd.DataFrame(rows)
    table['delta_aic'] = table['aic'] - table['aic'].min()
    table['delta_bic'] = table['bic'] - table['bic'].min()
    return table


def estimate_measurement_noise(x, magnetization, curve_type='backfield'):
    """
    Robustly estimate the measurement noise of a remanence curve.

    Suppresses the smooth signal and returns a robust standard deviation of
    the residual scatter, without any smoothing or model fitting. This
    provides the noise scale needed to judge when an unmixing model fits "to
    within the measurement noise" (see select_n_components).

    For each interior point the smooth signal is removed by comparing the
    point to the value predicted for it by cubic interpolation through its
    four nearest neighbours (two on each side) at their actual field
    positions; the residual is scaled by the standard deviation that
    combination would have under white noise, and a robust (median-absolute)
    scale is taken. Because the interpolation is exact for any polynomial of
    degree <= 3, this removes not just the local slope but the curvature of
    the sigmoidal curve, so the estimator is little biased even on the coarse
    and non-uniform (typically log-spaced) field grids of backfield/IRM
    measurements -- unlike a plain second difference, which cancels only a
    linear trend and inflates the noise where the curve bends.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT); the data are sorted by x internally.
    magnetization : array-like
        Remanence curve values at x.
    curve_type : str
        Unused; accepted for signature consistency with the unmixing
        functions.

    Returns
    -------
    float
        Estimated measurement noise standard deviation in magnetization
        units.
    """
    x = np.asarray(x, dtype=float)
    M = np.asarray(magnetization, dtype=float)
    order = np.argsort(x)
    x, M = x[order], M[order]
    if len(M) < 5:
        return float(np.std(M))
    # predict each interior point by cubic interpolation through its four
    # neighbours (i-2, i-1, i+1, i+2) at their true positions; the residual
    # cancels any signal up to a local cubic, so both slope and curvature of
    # the smooth curve are removed for arbitrary spacing
    c = np.arange(2, len(x) - 2)
    x0 = x[c]
    xa, xb, xc, xd = x[c - 2], x[c - 1], x[c + 1], x[c + 2]
    Ma, Mb, Mc, Md = M[c - 2], M[c - 1], M[c + 1], M[c + 2]

    def lagrange(xi, xj, xk, xl):
        # weight of the point at xi in the cubic interpolant evaluated at x0
        return ((x0 - xj) * (x0 - xk) * (x0 - xl)
                / ((xi - xj) * (xi - xk) * (xi - xl)))

    with np.errstate(divide='ignore', invalid='ignore'):
        La = lagrange(xa, xb, xc, xd)
        Lb = lagrange(xb, xa, xc, xd)
        Lc = lagrange(xc, xa, xb, xd)
        Ld = lagrange(xd, xa, xb, xc)
        residual = M[c] - (La * Ma + Lb * Mb + Lc * Mc + Ld * Md)
        # under white noise var(residual) = sigma^2 (1 + La^2 + Lb^2 + ...)
        scale = np.sqrt(1.0 + La ** 2 + Lb ** 2 + Lc ** 2 + Ld ** 2)
        normalized = np.abs(residual / scale)
    normalized = normalized[np.isfinite(normalized)]
    if normalized.size == 0:
        return float(np.std(M))
    return float(1.482602 * np.median(normalized))


def select_n_components(x, magnetization, method='curve', min_components=1,
                        max_components=4, criterion='parsimony',
                        min_improvement=0.02, noise_level=None,
                        reduced_chi2_target=1.0, curve_type='backfield',
                        vary_skew=False, verbose=False, **kwargs):
    """
    Choose the number of coercivity components by a parsimony rule.

    Fits models with a range of component counts and selects the simplest
    one that adequately describes the data. This is deliberately different
    from minimizing an information criterion or maximizing the Bayesian
    evidence: with high-resolution, low-noise curves those measures tend to
    keep favoring more components indefinitely, because a real coercivity
    distribution is never exactly log-Gaussian and each added component
    removes a little more systematic misfit. Following the parsimony
    principle emphasized by Egli (2003) and Heslop (2015), an extra
    component is accepted only when it produces a large enough improvement,
    so a simpler adequate model is preferred.

    Two selection criteria are provided:

    - 'parsimony' (default): an added component is retained only if it
      reduces the residual sum of squares by at least `min_improvement`
      times the baseline (single-component) residual. Because the second
      component typically removes most of the baseline misfit while a
      spurious third component removes only a tiny fraction of it, this
      robustly stops at the mineralogically meaningful count regardless of
      the noise level.
    - 'chi2': the simplest model whose reduced chi-square (using
      `noise_level`, estimated with estimate_measurement_noise if not
      given) falls at or below `reduced_chi2_target`, i.e. the simplest
      model that fits to within the measurement noise. The noise estimator
      is spacing-aware and unbiased on the coarse, log-spaced field grids of
      backfield/IRM data, but 'chi2' remains the less robust criterion: like
      the information criteria and the Bayesian evidence it tends to
      over-select on high-resolution, low-noise curves (once the noise is
      not over-estimated, any small departure of the data from a log-Gaussian
      pushes the reduced chi-square of a real-count model just above one), and
      it is sensitive to the residual scatter of the noise estimate. Prefer
      'parsimony', or supply a trusted `noise_level` and a `reduced_chi2_target`
      slightly above 1, when using it. For spectrum-space methods ('spectrum',
      'maxunmix', or a Bayesian fit with space='spectrum') the residuals and
      hence the noise are in dM/dlog10(B) units, so the noise is estimated on
      the finite-difference spectrum rather than the measured curve; that
      spectrum noise is mildly correlated, which the estimator does not model,
      making the spectrum-space chi2 more approximate still.

    In all cases the returned table reports the fit statistics, the
    fractional RSS improvement per added component, and (when a noise level
    is available) the reduced chi-square, so the selection can be inspected
    and overridden.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    magnetization : array-like
        Remanence curve values at x.
    method : str
        Registered unmixing method used for each fit (default 'curve').
    min_components, max_components : int
        Range of component counts to consider.
    criterion : str
        'parsimony' or 'chi2'.
    min_improvement : float
        For 'parsimony': minimum fraction of the baseline residual an added
        component must explain to be retained (default 0.02).
    noise_level : float, optional
        Measurement noise standard deviation for 'chi2'; estimated from the
        data if not given.
    reduced_chi2_target : float
        For 'chi2': the reduced chi-square at or below which a model is
        considered adequate (default 1.0).
    curve_type : str
        'backfield' or 'acquisition'.
    vary_skew : bool
        Whether skew varies during fitting.
    verbose : bool
        Print the selection outcome.
    **kwargs
        Passed to the unmixing method.

    Returns
    -------
    tuple
        (selected_n, table, results) where selected_n is the chosen number
        of components, table is a DataFrame of per-model statistics (with a
        boolean 'selected' column), and results maps component count ->
        result dictionary.
    """
    assert criterion in ('parsimony', 'chi2'), \
        "criterion must be 'parsimony' or 'chi2'"
    if method not in UNMIXING_METHODS:
        raise ValueError(f"unknown unmixing method '{method}'; available: "
                         f'{sorted(UNMIXING_METHODS)}')
    counts = list(range(min_components, max_components + 1))
    if len(counts) == 0:
        raise ValueError('max_components must be >= min_components')

    # The chi2 adequacy test compares the fit residual sum of squares to the
    # noise level, so the noise must be estimated in the SAME data space the
    # residuals live in. Spectrum-space methods ('spectrum', 'maxunmix', and
    # Bayesian fits with space='spectrum') fit dM/dlog10(B), not the measured
    # curve, so their rss is in spectrum units; estimating the noise on the
    # measured curve instead would mix units and inflate reduced_chi2 by the
    # (large) finite-difference amplification factor, defeating the criterion.
    # The spacing-aware estimator applied to the finite-difference spectrum
    # returns the spectrum-space noise scale directly, accounting for the
    # non-uniform log-grid spacing. (The finite-difference spectrum noise is
    # mildly correlated, which this white-noise estimator does not model, so
    # the spectrum-space chi2 is approximate -- consistent with chi2 being the
    # less robust criterion; see the note below.)
    fits_spectrum = (method in ('spectrum', 'maxunmix')
                     or (method == 'bayes' and kwargs.get('space') == 'spectrum'))
    if noise_level is None:
        if fits_spectrum:
            noise_x, noise_y = coercivity_spectrum_from_curve(
                x, magnetization, curve_type)
        else:
            noise_x, noise_y = x, magnetization
        noise_level = estimate_measurement_noise(noise_x, noise_y, curve_type)

    results = {}
    rows = []
    for K in counts:
        result = unmix_coercivity(x, magnetization, method=method,
                                  n_components=K, curve_type=curve_type,
                                  vary_skew=vary_skew, **kwargs)
        results[K] = result
        stats = result['stats']
        rows.append({
            'n_components': K,
            'n_params': stats['n_params'],
            'rss': stats['rss'],
            'r_squared': stats['r_squared'],
            'aic': stats['aic'],
            'bic': stats['bic'],
            'reduced_chi2': (stats['rss'] / (noise_level ** 2 * stats['dof'])
                             if stats['dof'] > 0 else np.nan),
        })
    table = pd.DataFrame(rows)

    baseline_rss = table['rss'].iloc[0]
    improvement = [np.nan]
    for i in range(1, len(table)):
        improvement.append((table['rss'].iloc[i - 1] - table['rss'].iloc[i])
                           / baseline_rss if baseline_rss > 0 else np.nan)
    table['rss_improvement_fraction'] = improvement

    if criterion == 'parsimony':
        selected = counts[0]
        for i in range(1, len(table)):
            if table['rss_improvement_fraction'].iloc[i] >= min_improvement:
                selected = counts[i]
            else:
                break
    else:  # chi2 adequacy
        adequate = table[table['reduced_chi2'] <= reduced_chi2_target]
        selected = (int(adequate['n_components'].iloc[0]) if len(adequate)
                    else counts[-1])

    table['selected'] = table['n_components'] == selected
    if verbose:
        print(f"selected {selected} component(s) by '{criterion}' criterion "
              f'(noise ~ {noise_level:.3g})')
    return selected, table, results


def unmixing_bootstrap(result, n_boot=500, resample='cases', proportion=1.0,
                       noise_level=None, random_seed=None, n_grid=200,
                       verbose=False):
    """
    Bootstrap uncertainty estimation for an unmixing result.

    Repeatedly refits the model to resampled data, starting each fit from
    the best-fit parameters, and summarizes the distributions of parameters
    and model curves. Two resampling schemes are available:

    - 'cases': data points are drawn with replacement ('proportion'
      controls the resample size relative to the data). With
      proportion=0.95 and noise_level=0.02 this emulates the resampling
      scheme of the MAX UnMix program (Maxbauer et al., 2016).
    - 'residuals': the best-fit curve is perturbed with resampled fit
      residuals, preserving the field spacing of the original data.

    Bootstrap distributions capture the full nonlinearity of the model and
    are generally more trustworthy than the linearized standard errors in
    the 'params' table, especially for strongly overlapping components.

    Parameters
    ----------
    result : dict
        Result from unmix_coercivity_spectrum or unmix_backfield_curve.
    n_boot : int
        Number of bootstrap replicates (default 500).
    resample : str
        'cases' or 'residuals'.
    proportion : float
        Fraction of the data resampled per replicate for 'cases' (default 1).
    noise_level : float, optional
        If given, multiplicative Gaussian noise with this relative standard
        deviation is added to each resampled dataset (MAX UnMix uses 0.02).
    random_seed : None, int, or numpy.random.Generator
        Seed for reproducibility.
    n_grid : int
        Number of grid points for the model-curve confidence bands.
    verbose : bool
        Print a progress summary.

    Returns
    -------
    dict
        A copy of the input result with an added 'bootstrap' entry
        containing 'param_summary' (per-component mean/std/percentiles for
        each parameter and derived quantity), 'curves' (percentile bands of
        the total and per-component model on 'x_grid'), 'n_success', and
        'param_samples' (the raw bootstrap parameter arrays).
    """
    assert resample in ('cases', 'residuals'), \
        "resample must be 'cases' or 'residuals'"
    assert 0 < proportion <= 1, 'proportion must be in (0, 1]'
    rng = _resolve_rng(random_seed)

    method = result['method']
    if method == 'bayes':
        raise ValueError(
            "unmixing_bootstrap does not apply to Bayesian results, which "
            "already carry full posterior uncertainty in "
            "result['bayes']['param_summary'] (credible intervals). To "
            "bootstrap a least-squares fit, pass a 'curve', 'spectrum', or "
            "'maxunmix' result instead.")
    # dispatch the refit on the stored fitting space, not the method name:
    # 'spectrum' and 'maxunmix' both fit the derivative spectrum, so both
    # must be refit with the spectrum model (keying on method == 'spectrum'
    # alone sent maxunmix results through the cumulative-curve branch)
    fits_spectrum = _result_is_spectrum(result)
    x, y = result['x'], result['y']
    curve_type = result['curve_type']
    vary_skew = result['vary_skew']
    K = result['n_components']
    best = result['params'][UNMIX_PARAM_COLUMNS].copy().reset_index(drop=True)
    n = len(x)
    n_sample = max(int(n * proportion), 3 * K + 2)

    x_grid = np.linspace(x.min(), x.max(), n_grid)
    tracked = ['contribution', 'proportion', 'location', 'dp', 'skew',
               'sd_log', 'B_mean_mT', 'B_median_mT', 'B_peak_mT']
    samples = {name: [] for name in tracked}
    total_curves = []
    comp_curves = []
    n_success = 0

    for _ in range(n_boot):
        if resample == 'cases':
            idx = rng.choice(n, size=n_sample, replace=True)
            xb, yb = x[idx], y[idx]
        else:
            perturbation = rng.choice(result['residuals'], size=n,
                                      replace=True)
            xb, yb = x, result['y_fit'] + perturbation
        if noise_level is not None:
            yb = yb * (1.0 + rng.normal(0.0, noise_level, size=len(yb)))
        try:
            if fits_spectrum:
                fit = unmix_coercivity_spectrum(xb, yb,
                                                initial_parameters=best,
                                                vary_skew=vary_skew)
            else:
                fit = unmix_backfield_curve(xb, yb, initial_parameters=best,
                                            curve_type=curve_type,
                                            vary_skew=vary_skew)
        except (ValueError, RuntimeError):
            continue
        if not fit['success']:
            continue
        # components are sorted by mean coercivity within each fit, which
        # aligns replicate components with the reference ordering
        p = fit['params']
        for name in tracked:
            samples[name].append(p[name].to_numpy())
        arr = p[UNMIX_PARAM_COLUMNS].to_numpy()
        if fits_spectrum:
            total_curves.append(coercivity_spectrum_model(x_grid, arr))
            comp_curves.append(coercivity_spectrum_components(x_grid, arr))
        else:
            total_curves.append(coercivity_curve_model(
                x_grid, arr, offset=fit['offset'], curve_type=curve_type))
            comp_curves.append(coercivity_curve_components(
                x_grid, arr, curve_type=curve_type))
        n_success += 1

    if n_success < max(10, n_boot // 10):
        raise RuntimeError(f'only {n_success} of {n_boot} bootstrap '
                           'replicates converged; check the fit or initial '
                           'parameters')
    if verbose:
        print(f'{n_success}/{n_boot} bootstrap replicates converged')

    percentiles = [2.5, 50, 97.5]
    summary_rows = []
    for comp in range(K):
        row = {'component': comp + 1}
        for name in tracked:
            vals = np.array([s[comp] for s in samples[name]])
            row[f'{name}_mean'] = vals.mean()
            row[f'{name}_std'] = vals.std()
            for pct in percentiles:
                row[f'{name}_p{str(pct).replace(".", "_")}'] = \
                    np.percentile(vals, pct)
        summary_rows.append(row)
    param_summary = pd.DataFrame(summary_rows).set_index('component')

    total_curves = np.array(total_curves)
    comp_curves = np.array(comp_curves)
    curves = {
        'x_grid': x_grid,
        'total_p2_5': np.percentile(total_curves, 2.5, axis=0),
        'total_p50': np.percentile(total_curves, 50, axis=0),
        'total_p97_5': np.percentile(total_curves, 97.5, axis=0),
        'components_p2_5': np.percentile(comp_curves, 2.5, axis=0),
        'components_p50': np.percentile(comp_curves, 50, axis=0),
        'components_p97_5': np.percentile(comp_curves, 97.5, axis=0),
    }

    result_out = copy.deepcopy(result)
    result_out['bootstrap'] = {
        'n_boot': n_boot,
        'n_success': n_success,
        'resample': resample,
        'proportion': proportion,
        'noise_level': noise_level,
        'param_summary': param_summary,
        'param_samples': {name: np.array(vals)
                          for name, vals in samples.items()},
        'curves': curves,
    }
    return result_out


def unmixing_multistart(x, magnetization, method='spectrum', n_components=2,
                        n_starts=100, vary_skew=False, curve_type='backfield',
                        random_seed=None, location_tolerance=0.1,
                        proportion_tolerance=0.05, verbose=False, **kwargs):
    """
    Map the distinct unmixing solutions reachable from many initializations.

    Coercivity unmixing is a non-convex problem: fits started from
    different initial parameters can converge to different local minima
    that describe the data almost equally well. A single fit (and a
    bootstrap of it, which restarts every replicate from the best-fit
    values) is conditioned on one solution basin and therefore hides this
    non-uniqueness. This function launches the fit from n_starts dispersed
    random initializations (plus the automatic peak-detection estimate),
    clusters the converged solutions, and reports each distinct solution
    with its fit statistics and Akaike weight, making the degeneracy of
    the decomposition explicit.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    magnetization : array-like
        Remanence curve values at x (e.g. 'magn_mass_shift').
    method : str
        Registered unmixing method used for each fit (default 'spectrum').
    n_components : int
        Number of components (default 2).
    n_starts : int
        Number of random initializations (default 100).
    vary_skew : bool
        Whether skew varies during fitting; random starts draw skew from
        [-5, 5] when True.
    curve_type : str
        'backfield' or 'acquisition'.
    random_seed : None, int, or numpy.random.Generator
        Seed for reproducible starting points.
    location_tolerance : float
        Two solutions are considered the same when all component
        locations agree within this tolerance (log10 units, default 0.1)
        and all proportions agree within proportion_tolerance.
    proportion_tolerance : float
        Proportion agreement tolerance (default 0.05).
    verbose : bool
        Print a summary of the distinct solutions.
    **kwargs
        Passed through to the unmixing method.

    Returns
    -------
    dict
        The best (lowest RSS) result dictionary, augmented with a
        'multistart' entry containing 'solutions' (a DataFrame with one
        row per distinct solution: n_hits, rss, r_squared, aic,
        delta_aic, akaike_weight, and per-component B_mean_mT / sd_log /
        proportion columns), 'results' (the representative result
        dictionary for each solution, in the same order), 'n_starts', and
        'n_converged'.
    """
    if method not in UNMIXING_METHODS:
        raise ValueError(f"unknown unmixing method '{method}'; available: "
                         f'{sorted(UNMIXING_METHODS)}')
    rng = _resolve_rng(random_seed)
    x = np.asarray(x, dtype=float)
    M = np.asarray(magnetization, dtype=float)
    x_mid, spectrum = coercivity_spectrum_from_curve(x, M, curve_type)
    total_area = np.abs(_trapz(spectrum, x_mid))
    K = n_components

    starting_tables = [None]  # None -> automatic estimation inside the method
    lo, hi = x.min() + 0.05, x.max() - 0.05
    for _ in range(n_starts):
        locations = np.sort(rng.uniform(lo, hi, size=K))
        dps = np.exp(rng.uniform(np.log(0.03), np.log(0.8), size=K))
        proportions = rng.dirichlet(np.ones(K))
        skews = rng.uniform(-5, 5, size=K) if vary_skew else np.zeros(K)
        starting_tables.append(pd.DataFrame({
            'contribution': proportions * total_area,
            'location': locations,
            'dp': dps,
            'skew': skews,
        }))

    fits = []
    for table in starting_tables:
        try:
            fit = unmix_coercivity(x, M, method=method,
                                   n_components=K if table is None else None,
                                   initial_parameters=table,
                                   curve_type=curve_type,
                                   vary_skew=vary_skew, **kwargs)
        except (ValueError, RuntimeError):
            continue
        if fit['success'] and np.isfinite(fit['stats']['rss']):
            fits.append(fit)
    if not fits:
        raise RuntimeError('no multistart fits converged')

    # cluster converged fits into distinct solutions (best fit first)
    fits.sort(key=lambda f: f['stats']['rss'])
    clusters = []  # list of dicts: {'representative': fit, 'n_hits': int}
    for fit in fits:
        locations = fit['params']['location'].to_numpy()
        proportions = fit['params']['proportion'].to_numpy()
        for cluster in clusters:
            ref = cluster['representative']['params']
            same_location = np.all(np.abs(
                locations - ref['location'].to_numpy()) <= location_tolerance)
            same_proportion = np.all(np.abs(
                proportions - ref['proportion'].to_numpy())
                <= proportion_tolerance)
            if same_location and same_proportion:
                cluster['n_hits'] += 1
                break
        else:
            clusters.append({'representative': fit, 'n_hits': 1})

    aics = np.array([c['representative']['stats']['aic'] for c in clusters])
    delta_aic = aics - aics.min()
    with np.errstate(over='ignore'):
        weights = np.exp(-0.5 * delta_aic)
    weights = weights / weights.sum()

    rows = []
    for i, cluster in enumerate(clusters):
        fit = cluster['representative']
        row = {
            'solution': i + 1,
            'n_hits': cluster['n_hits'],
            'rss': fit['stats']['rss'],
            'r_squared': fit['stats']['r_squared'],
            'aic': fit['stats']['aic'],
            'delta_aic': delta_aic[i],
            'akaike_weight': weights[i],
        }
        for comp_index, prow in fit['params'].iterrows():
            row[f'B_mean_mT_c{comp_index}'] = prow['B_mean_mT']
            row[f'sd_log_c{comp_index}'] = prow['sd_log']
            row[f'proportion_c{comp_index}'] = prow['proportion']
        rows.append(row)
    solutions = pd.DataFrame(rows).set_index('solution')

    if verbose:
        print(f'{len(fits)}/{len(starting_tables)} fits converged; '
              f'{len(clusters)} distinct solution(s)')

    best = copy.deepcopy(clusters[0]['representative'])
    best['multistart'] = {
        'solutions': solutions,
        'results': [c['representative'] for c in clusters],
        'n_starts': len(starting_tables),
        'n_converged': len(fits),
        'method': method,
    }
    return best


# Bayesian unmixing via nested sampling
# ------------------------------------------------------------------------------------------------------------------

def _check_dynesty():
    try:
        import dynesty  # noqa: F401
    except ImportError:
        raise ImportError(
            'dynesty is required for Bayesian unmixing. '
            'Install it with: pip install dynesty')


def _ordered_uniform_transform(u, low, high):
    """
    Map unit-cube draws to ordered uniform order statistics on [low, high].

    Uses the standard recursive inverse-CDF construction so that the
    returned values are jointly distributed as the order statistics of K
    independent uniforms, which enforces component ordering (and thereby
    removes label switching) without distorting the prior.
    """
    K = len(u)
    ordered = np.empty(K)
    upper = 1.0
    for k in range(K - 1, -1, -1):
        upper = upper * u[k] ** (1.0 / (k + 1))
        ordered[k] = upper
    return low + (high - low) * ordered


def unmix_coercivity_bayes(x, magnetization, n_components=2,
                           curve_type='backfield', space='curve',
                           vary_skew=False,
                           fit_offset=True, priors=None, nlive=250,
                           dlogz=0.1, sample='rslice', random_seed=None,
                           n_grid=200, n_posterior_curves=300,
                           verbose=False):
    """
    Bayesian coercivity unmixing by nested sampling (requires dynesty).

    The remanence data are modeled as a sum of skew-normal components, with
    the noise standard deviation treated as a free parameter, and sampled
    with static nested sampling (Skilling, 2006) as implemented in dynesty
    (Speagle, 2020), which also returns the Bayesian evidence (logz) -- the
    principled criterion for choosing the number of components (compare logz
    between runs with different n_components). The fit can be performed in
    either of two data spaces (see the `space` argument):

    - space='curve' (default): the measured curve M(B) is fit directly with
      cumulative skew-normal components plus a constant offset. An
      independent Gaussian noise model is defensible here, and no numerical
      differentiation is required. This is the more conservative choice.
    - space='spectrum': the finite-difference coercivity spectrum
      dM/dlog10(B) is fit with skew-normal densities (no offset). Fitting the
      derivative directly reproduces the coercivity-distribution peak that a
      curve fit can under-represent, and lets skewness be constrained by the
      peak shape. The trade-off is that differencing correlates adjacent
      points, so the i.i.d. Gaussian likelihood used here is an approximation
      (the same one the least-squares and MAX UnMix spectrum fits make);
      credible intervals in this space should be read with that caveat.

    The component parameterization (contribution=area, location, dp, skew) is
    identical in both spaces, so their results are directly comparable, and
    comparing them is a useful robustness check.

    Unlike bootstrap resampling of a single fit, the posterior represents
    the full range of component decompositions consistent with the data
    and priors: parameter trade-offs between overlapping components appear
    as wide, correlated, and possibly multimodal posterior distributions
    rather than being hidden by a single optimizer solution.

    Component locations are sampled as ordered order-statistics, which
    fixes component labels without distorting the prior. Default priors
    are weakly informative (locations uniform across the measured field
    range, dispersions log-uniform on [0.02, 1.0] decades, contributions
    uniform up to ~3x the data range); mineralogical knowledge can be
    injected through the priors argument.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT).
    magnetization : array-like
        Remanence curve values at x (e.g. 'magn_mass_shift').
    n_components : int
        Number of components (default 2).
    curve_type : str
        'backfield' or 'acquisition'.
    space : str
        'curve' (fit the measured curve, default) or 'spectrum' (fit the
        finite-difference dM/dlog10(B) spectrum). See the summary above for
        the trade-offs; with space='spectrum' the offset is not used.
    vary_skew : bool
        Sample component skew (uniform prior on [-10, 10]); default False
        (symmetric log-Gaussian components).
    fit_offset : bool
        Include a constant baseline offset (default True; ignored when
        space='spectrum').
    priors : dict, optional
        Overrides for the default prior bounds. Recognized keys:
        'mean', 'location', 'dp', 'contribution', 'skew' map to a list
        of (low, high) tuples, one per component (in log10 units for
        'mean'/'location'/'dp', magnetization units for 'contribution');
        'offset' and 'noise' map to a single (low, high) tuple in
        magnetization units. A 'mean' window constrains each component's
        MEAN coercivity (log10 mT): the mean is sampled uniformly in the
        window and the skew-normal location is derived from the sampled dp
        and skew, so the window means what it says even for skewed
        components (this is what mineral_priors produces). A 'location'
        window instead constrains the raw location parameter directly.
        Either replaces the weakly-informative ordered-uniform default, so
        the windows should be non-overlapping or ordered to keep component
        labels meaningful. 'mean' takes precedence over 'location' if both
        are given.
    nlive : int
        Number of live points (default 250).
    dlogz : float
        Evidence convergence tolerance (default 0.1).
    sample : str
        dynesty sampling method (default 'rslice'). Slice sampling is
        robust to the thin, curved likelihood ridges that overlapping
        components produce; the dynesty default uniform-ellipsoid
        sampler can stall on such geometries.
    random_seed : None, int, or numpy.random.Generator
        Seed for reproducibility.
    n_grid : int
        Grid size for posterior model bands.
    n_posterior_curves : int
        Number of posterior draws used for the model bands (default 300).
    verbose : bool
        Show dynesty progress.

    Returns
    -------
    dict
        Standardized result dictionary (parameters set to posterior
        medians) with an added 'bayes' entry containing 'param_summary'
        (per-component posterior mean/std/percentiles, same format as the
        bootstrap summary), 'samples' (equally weighted posterior draws
        for every parameter and derived quantity), 'logz', 'logzerr',
        'noise' (posterior median noise standard deviation), and 'curves'
        (posterior percentile bands of the model).
    """
    _check_dynesty()
    import dynesty
    assert curve_type in ('backfield', 'acquisition'), \
        "curve_type must be 'backfield' or 'acquisition'"
    assert space in ('curve', 'spectrum'), \
        "space must be 'curve' or 'spectrum'"
    rng = _resolve_rng(random_seed)
    priors = dict(priors or {})

    x = np.asarray(x, dtype=float)
    y = np.asarray(magnetization, dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    x, y = x[finite], y[finite]
    if space == 'spectrum':
        # fit the finite-difference spectrum dM/dlog10(B); there is no
        # baseline offset in derivative space
        x, y = coercivity_spectrum_from_curve(x, y, curve_type)
        fit_offset = False
    y_scale = np.max(np.abs(y))
    if y_scale == 0:
        raise ValueError('magnetization data are all zero')
    ys = y / y_scale
    K = n_components
    n_data = len(x)

    def _forward(params, offset):
        if space == 'spectrum':
            return coercivity_spectrum_model(x, params)
        return coercivity_curve_model(x, params, offset=offset,
                                      curve_type=curve_type)

    def _forward_components(grid, params):
        if space == 'spectrum':
            return coercivity_spectrum_components(grid, params)
        return coercivity_curve_components(grid, params, curve_type=curve_type)

    # prior bounds (normalized units for contribution/offset/noise)
    # A component's coercivity window can be given either directly on the
    # skew-normal 'location' parameter, or -- preferably, and as produced by
    # mineral_priors -- on the component's MEAN coercivity via 'mean'. For a
    # skewed component the location is not itself a physical coercivity, so a
    # 'mean' window keeps the constraint on the reported mean coercivity
    # (10**mean_log): the mean is sampled uniformly in the window and the
    # location is derived from the sampled dp and skew.
    mean_bounds = priors.get('mean')
    if mean_bounds is not None:
        mean_bounds = [tuple(b) for b in mean_bounds]
        assert len(mean_bounds) == K
    location_bounds = priors.get('location')
    if location_bounds is not None:
        location_bounds = [tuple(b) for b in location_bounds]
        assert len(location_bounds) == K
    location_range = (x.min() - 0.2, x.max() + 0.2)
    dp_bounds = priors.get('dp', [(0.02, 1.0)] * K)
    contribution_bounds = [(low / y_scale, high / y_scale) for low, high in
                           priors.get('contribution',
                                      [(0.0, 3.0 * y_scale)] * K)]
    skew_bounds = priors.get('skew', [(-10.0, 10.0)] * K)
    offset_low, offset_high = np.array(
        priors.get('offset', (-0.2 * y_scale, 0.2 * y_scale))) / y_scale
    noise_low, noise_high = np.array(
        priors.get('noise', (1e-4 * y_scale, 0.3 * y_scale))) / y_scale

    ndim = 3 * K + (K if vary_skew else 0) + (1 if fit_offset else 0) + 1

    # unit-cube layout: contributions[0:K], locations[K:2K], dps[2K:3K],
    # skews[3K:4K] (if vary_skew), offset, noise. dps and skews are drawn
    # before locations so that a 'mean' window can derive the location from
    # the sampled dp and skew.
    def prior_transform(u):
        theta = np.empty(ndim)
        for k in range(K):  # contributions
            low, high = contribution_bounds[k]
            theta[k] = low + (high - low) * u[k]
        for k in range(K):  # dispersions, log-uniform
            low, high = dp_bounds[k]
            theta[2 * K + k] = np.exp(np.log(low)
                                      + (np.log(high) - np.log(low))
                                      * u[2 * K + k])
        if vary_skew:
            for k in range(K):
                low, high = skew_bounds[k]
                theta[3 * K + k] = low + (high - low) * u[3 * K + k]
            skew_vals = theta[3 * K:4 * K]
        else:
            skew_vals = np.zeros(K)
        if mean_bounds is not None:  # window on the mean coercivity
            delta = skew_vals / np.sqrt(1.0 + skew_vals ** 2)
            shift = theta[2 * K:3 * K] * delta * np.sqrt(2.0 / np.pi)
            for k in range(K):
                low, high = mean_bounds[k]
                mean_log = low + (high - low) * u[K + k]
                theta[K + k] = mean_log - shift[k]  # location = mean - shift
        elif location_bounds is not None:  # window on the location parameter
            for k in range(K):
                low, high = location_bounds[k]
                theta[K + k] = low + (high - low) * u[K + k]
        else:  # ordered locations (weakly informative default)
            theta[K:2 * K] = _ordered_uniform_transform(
                u[K:2 * K], location_range[0], location_range[1])
        i = 4 * K if vary_skew else 3 * K
        if fit_offset:
            theta[i] = offset_low + (offset_high - offset_low) * u[i]
            i += 1
        theta[i] = np.exp(np.log(noise_low)
                          + (np.log(noise_high) - np.log(noise_low)) * u[i])
        return theta

    def unpack(theta):
        c = theta[:K]
        loc = theta[K:2 * K]
        dp = theta[2 * K:3 * K]
        i = 3 * K
        if vary_skew:
            skew = theta[i:i + K]
            i += K
        else:
            skew = np.zeros(K)
        offset = theta[i] if fit_offset else 0.0
        noise = theta[-1]
        return c, loc, dp, skew, offset, noise

    log_norm = -0.5 * n_data * np.log(2.0 * np.pi)

    def loglike(theta):
        c, loc, dp, skew, offset, noise = unpack(theta)
        params = np.column_stack([c, loc, dp, skew])
        model = _forward(params, offset)
        residual = (model - ys) / noise
        value = log_norm - n_data * np.log(noise) \
            - 0.5 * float(residual @ residual)
        return value if np.isfinite(value) else -1e300

    sampler = dynesty.NestedSampler(loglike, prior_transform, ndim,
                                    nlive=nlive, sample=sample, rstate=rng)
    sampler.run_nested(dlogz=dlogz, print_progress=verbose)
    ns_results = sampler.results
    samples = ns_results.samples_equal(rstate=rng)

    # per-draw derived quantities (analytic, vectorized)
    contributions = samples[:, :K] * y_scale
    locations = samples[:, K:2 * K]
    dps = samples[:, 2 * K:3 * K]
    skews = samples[:, 3 * K:4 * K] if vary_skew else np.zeros_like(locations)
    offsets = (samples[:, -2] * y_scale if fit_offset
               else np.zeros(len(samples)))
    noises = samples[:, -1] * y_scale
    deltas = skews / np.sqrt(1.0 + skews ** 2)
    means_log = locations + dps * deltas * np.sqrt(2.0 / np.pi)
    sd_logs = dps * np.sqrt(1.0 - 2.0 * deltas ** 2 / np.pi)
    proportions = contributions / contributions.sum(axis=1, keepdims=True)
    derived = {
        'contribution': contributions,
        'proportion': proportions,
        'location': locations,
        'dp': dps,
        'skew': skews,
        'sd_log': sd_logs,
        'B_mean_mT': 10 ** means_log,
    }

    percentiles = [2.5, 50, 97.5]
    summary_rows = []
    for comp in range(K):
        row = {'component': comp + 1}
        for name, values in derived.items():
            column = values[:, comp]
            row[f'{name}_mean'] = column.mean()
            row[f'{name}_std'] = column.std()
            for pct in percentiles:
                row[f'{name}_p{str(pct).replace(".", "_")}'] = \
                    np.percentile(column, pct)
        summary_rows.append(row)
    param_summary = pd.DataFrame(summary_rows).set_index('component')

    # posterior-median parameter table in the standard result format
    median_params = np.column_stack([
        np.median(contributions, axis=0), np.median(locations, axis=0),
        np.median(dps, axis=0), np.median(skews, axis=0)])
    offset_median = float(np.median(offsets))
    rows = []
    for comp in range(K):
        c_med, loc_med, dp_med, skew_med = median_params[comp]
        stats_comp = skewnormal_stats(loc_med, dp_med, skew_med)
        rows.append({
            'contribution': c_med,
            'se_contribution': contributions[:, comp].std(),
            'location': loc_med,
            'se_location': locations[:, comp].std(),
            'dp': dp_med,
            'se_dp': dps[:, comp].std(),
            'skew': skew_med,
            'se_skew': skews[:, comp].std(),
            'sd_log': stats_comp['std'],
            'log10_B_mean': stats_comp['mean'],
            'B_mean_mT': 10 ** stats_comp['mean'],
            'B_median_mT': 10 ** stats_comp['median'],
            'B_peak_mT': 10 ** stats_comp['mode'],
        })
    params = pd.DataFrame(rows, index=pd.RangeIndex(1, K + 1,
                                                    name='component'))
    total = params['contribution'].sum()
    params.insert(1, 'proportion', params['contribution'] / total)

    y_fit = _forward(median_params, offset_median)
    residuals = y - y_fit
    rss = float(np.sum(residuals ** 2))
    tss = float(np.sum((y - y.mean()) ** 2))
    n_params = ndim
    stats = {
        'n': n_data,
        'n_params': n_params,
        'dof': n_data - n_params,
        'rss': rss,
        'r_squared': 1.0 - rss / tss if tss > 0 else np.nan,
        'reduced_chi_square': (rss / (n_data - n_params)
                               if n_data > n_params else np.nan),
        'aic': np.nan,  # use logz for Bayesian model comparison
        'bic': np.nan,
        'logz': float(ns_results.logz[-1]),
        'logzerr': float(ns_results.logzerr[-1]),
    }

    # posterior model bands from a subset of equally weighted draws
    x_grid = np.linspace(x.min(), x.max(), n_grid)
    n_draws = min(n_posterior_curves, len(samples))
    draw_index = rng.choice(len(samples), size=n_draws, replace=False)
    total_curves = np.empty((n_draws, n_grid))
    comp_curves = np.empty((n_draws, K, n_grid))
    for j, index in enumerate(draw_index):
        draw_params = np.column_stack([
            contributions[index], locations[index], dps[index],
            skews[index]])
        comps = _forward_components(x_grid, draw_params)
        comp_curves[j] = comps
        total_curves[j] = comps.sum(axis=0) + offsets[index]
    curves = {
        'x_grid': x_grid,
        'total_p2_5': np.percentile(total_curves, 2.5, axis=0),
        'total_p50': np.percentile(total_curves, 50, axis=0),
        'total_p97_5': np.percentile(total_curves, 97.5, axis=0),
        'components_p2_5': np.percentile(comp_curves, 2.5, axis=0),
        'components_p50': np.percentile(comp_curves, 50, axis=0),
        'components_p97_5': np.percentile(comp_curves, 97.5, axis=0),
    }

    initial_df = pd.DataFrame(median_params, columns=UNMIX_PARAM_COLUMNS)
    return {
        'method': 'bayes',
        'space': space,
        'curve_type': curve_type,
        'n_components': K,
        'success': True,
        'message': (f'nested sampling converged '
                    f'(logz = {stats["logz"]:.2f} '
                    f'+/- {stats["logzerr"]:.2f})'),
        'params': params,
        'offset': offset_median,
        'se_offset': float(np.std(offsets)),
        'x': x,
        'y': y,
        'y_fit': y_fit,
        'residuals': residuals,
        'weights': None,
        'stats': stats,
        'initial_parameters': initial_df,
        'vary_skew': vary_skew,
        'bayes': {
            'param_summary': param_summary,
            'samples': {**{name: values for name, values in derived.items()},
                        'offset': offsets, 'noise': noises},
            'logz': stats['logz'],
            'logzerr': stats['logzerr'],
            'noise': float(np.median(noises)),
            'ncall': int(ns_results.ncall.sum()),
            'niter': int(ns_results.niter),
            'nlive': nlive,
            'curves': curves,
        },
    }


def _unmix_method_bayes(x, magnetization, n_components=None,
                        initial_parameters=None, curve_type='backfield',
                        vary_skew=False, priors=None, **kwargs):
    """
    Registered 'bayes' method: nested-sampling posterior in measurement
    space. If initial_parameters are supplied (e.g. from the interactive
    widget) and no explicit priors are given, per-component location and
    dispersion priors are centered on them.
    """
    # a priors dict from mineral_priors() carries one entry per component
    # (as a 'mean' or 'location' window), so n_components can be inferred
    if n_components is None and priors is not None:
        for key in ('mean', 'location'):
            if priors.get(key) is not None:
                n_components = len(priors[key])
                break
    if initial_parameters is not None:
        if n_components is None:
            n_components = len(initial_parameters)
        if priors is None:
            table = _unmix_parameters_to_array(initial_parameters)
            order = np.argsort(table[:, 1])
            table = table[order]
            priors = {
                'location': [(row[1] - max(3 * row[2], 0.3),
                              row[1] + max(3 * row[2], 0.3))
                             for row in table],
                'dp': [(max(row[2] / 4, 0.02), min(row[2] * 4, 1.5))
                       for row in table],
            }
    if n_components is None:
        raise ValueError('specify n_components, initial_parameters, or priors')
    return unmix_coercivity_bayes(x, magnetization,
                                  n_components=n_components,
                                  curve_type=curve_type,
                                  vary_skew=vary_skew, priors=priors,
                                  **kwargs)


UNMIXING_METHODS['bayes'] = _unmix_method_bayes


# Coercivity component prior library
# ------------------------------------------------------------------------------------------------------------------
# Characteristic coercivity ranges for common remanence-carrying magnetic
# mineral components, for use as informative priors in Bayesian unmixing
# (unmix_coercivity_bayes) or as initial parameters for the least-squares
# methods. Covered minerals: magnetite (igneous, detrital, eolian,
# pedogenic/extracellular, and biogenic soft/hard), maghemite (pure/soft and
# oxidized-magnetite/hard), the ferrimagnetic iron sulphides greigite and
# pyrrhotite, and the antiferromagnetic hematite (pigmentary/detrital).
#
# GOETHITE is deliberately NOT included. It does not magnetically saturate even
# in ~57 T fields (Roberts 2025, p. 337; only ~2-10% of its Mr is acquired by
# 3 T), so an ordinary backfield or IRM coercivity spectrum sees only an
# ambiguous low-coercivity tail that overlaps hematite and cannot quantify
# goethite; a fitted "goethite" component would be a poorly-constrained minimum
# estimate that invites over-interpretation. A high-coercivity component that
# might be goethite is better flagged and confirmed by independent thermal or
# low-temperature methods (see goethite_removal).
#
# Each entry gives, as (low, high) bounds of a uniform prior:
#   'B_median_mT' : the characteristic (median ~ mean) coercivity window, mT.
#                   mineral_priors passes this to unmix_coercivity_bayes as a
#                   'mean' window, so it constrains the component's MEAN
#                   coercivity (10**B_mean_mT) directly, whatever its skew.
#   'dp'          : the dispersion (one standard deviation of the log10-field
#                   distribution), log10 units.
#   'skew'        : the Azzalini skew-normal shape parameter (alpha), SIGNED
#                   by the physical asymmetry (see below). NB alpha is not the
#                   moment skewness; |alpha|~2-5 gives a visibly skewed
#                   component, alpha=0 is a symmetric log-Gaussian.
#
# SOURCES AND SHAPE CONVENTIONS:
#  * Numeric coercivity (B_median) and width (dp) ranges: the magnetite-family
#    and maghemite/loess values are from Egli (2003; 2004a Stud. Geophys.
#    Geod. 48, 391-446) component analysis of AF-demagnetized ARM/IRM (MDF and
#    DP), cross-checked against the grain-size systematics in Roberts (2025)
#    "Mineral Magnetism" (magnetite pp. 105-141, maghemite pp. 284-321).
#    Hematite, greigite, and pyrrhotite coercivity ranges are from Roberts
#    (2025) (hematite pp. 182-228, 267-283; sulphides pp. 356-416).
#    IMPORTANT: Roberts (2025) does NOT tabulate DP
#    or skew; the dp windows are therefore taken from / consistent with Egli
#    (2003, 2004a,b), Robertson & France (1994), and Kruiver et al. (2001),
#    not from Roberts, and are deliberately broad.
#  * SKEW SIGN (Roberts 2025, p. 117; Egli 2003, 2004b): coercivity
#    distributions of stable-SD, MD, and interacting magnetite (and maghemite)
#    are NEGATIVELY (left-) skewed on the log-field axis -- a heavier
#    low-field tail -- so those entries use alpha in roughly [-5, 0].
#    Pyrrhotite is POSITIVELY (right-) skewed (a hard, high-field tail; Roberts
#    p. 374), so alpha in roughly [-1, 5]. Greigite (SD) is near-symmetric,
#    left-skewed when SP/MD is present
#    (Roberts pp. 405-406). Hematite is variable (pigmentary components are
#    often fit skew-right, Maxbauer et al. 2016), so a broad two-sided window
#    is used. These signs are qualitative in Roberts; no numeric skew exists
#    to cite.
#
# IMPORTANT CAVEATS:
#  * A coercivity prior constrains a WINDOW, it does not identify a mineral.
#    The windows overlap: greigite (both saturate <0.3 T) and non-SD
#    pyrrhotite overlap magnetite/maghemite (Roberts pp. 405-407, 374), and
#    hard SD / metamorphic pyrrhotite overlaps pigmentary hematite.
#  * The characteristic coercivity depends on HOW it is measured, and the
#    ordering is systematic. For submicron magnetite Dunlop (1986, EPSL 78,
#    288-295, doi:10.1016/0012-821X(86)90068-3) measured Hc < MDF (the AF
#    median destructive field, i.e. the
#    Egli values) < Bcr (the backfield remanent coercive force) < the median
#    IRM-acquisition field, with the backfield Bcr running ~1.3-1.5x and the
#    acquisition median ~2x the AF-MDF (e.g. a 0.1-0.2 um PSD magnetite: MDF
#    ~18 mT, Bcr ~27-28 mT, acquisition ~39-41 mT). rockmagpy unmixing fits
#    the backfield or IRM coercivity distribution, whose median is the Bcr or
#    acquisition field, so a window taken from an AF-demagnetization component
#    analysis (the magnetite family, from Egli) sits somewhat low for these
#    curves. Treat the windows as soft, approximate priors, not calibrations,
#    and read the finer-is-harder-but-narrower trend of Dunlop (1986) as the
#    reason biogenic/pedogenic (fine) magnetite has both higher coercivity and
#    lower dp than coarse detrital magnetite.
#  * Pyrrhotite does not fully saturate in ordinary laboratory fields (>2 T to
#    saturate; Roberts p. 374), so a typical backfield/IRM experiment (<= 2-5
#    T) captures only its lower-coercivity part and UNDERESTIMATES its
#    contribution; pass field_max_mT to keep priors within the measured range
#    and read any such contribution as a minimum. (Goethite is unsaturated even
#    at 57 T, far more extreme, and is excluded from the library for that
#    reason -- see the header.)
#  * Hematite coercivity is grain-size controlled (Ozdemir & Dunlop 2014,
#    Hc ~ d^-0.61): across the fitting-relevant range of ~100s of nm
#    (pigmentary, fine specular) to ~100s of um (coarse specular) it runs from
#    ~1 T down to ~100-200 mT, so finer hematite is harder. (The very soft
#    Bcr of mm-scale single crystals is not a natural sedimentary population.)
#    Al-substitution raises hematite coercivity up to ~7-13 mol% Al and then
#    lowers it at high substitution, but this trend is strongly confounded by
#    covarying grain size (Roberts pp. 271-272).
#  * Component fitting near the SP/SD threshold can produce a spurious
#    low-coercivity component (Heslop et al., 2004); an unexpectedly soft
#    component should be checked against independent evidence.
#  * Ranges are deliberately generous (roughly the spread of the cited
#    populations, not a single sample). Narrow them with the `tighten`
#    argument of mineral_priors only when justified by independent data.
COERCIVITY_COMPONENT_LIBRARY = {
    'magnetite_pedogenic': {
        'B_median_mT': (10.0, 25.0), 'dp': (0.25, 0.40),
        'skew': (-5.0, 0.0),
        'source': 'Egli (2004a) components PD/EX (MDF ~17-18 mT, DP ~0.3); '
                  'Roberts (2025) p. 112 (unstrained, fine, soft) -- note '
                  'Roberts p. 285/301 considers pedogenic ferrimagnet often '
                  'to be maghemite rather than magnetite',
        'note': 'ultrafine SP-SSD magnetite; soft, narrow, left-skewed'},
    'magnetite_detrital': {
        'B_median_mT': (15.0, 45.0), 'dp': (0.30, 0.45),
        'skew': (-5.0, 0.0),
        'source': 'Egli (2004a) component D (AF MDF ~25-33 mT, DP ~0.35-0.40); '
                  'Dunlop (1986, doi:10.1016/0012-821X(86)90068-3) measured '
                  'submicron PSD magnetite (0.1-0.22 um) backfield Bcr ~27-28 '
                  'mT and median IRM-acquisition field ~39-41 mT, with broader '
                  'spectra for coarser grains; Roberts (2025) pp. 112, 121',
        'note': 'coarse detrital magnetite in water-lain sediments; '
                'broad/mixed, left-skewed. Backfield Bcr and IRM-acquisition '
                'medians run above the AF MDF (see the library caveats)'},
    'magnetite_igneous': {
        'B_median_mT': (8.0, 45.0), 'dp': (0.20, 0.50),
        'skew': (-5.0, 0.0),
        'source': 'Roberts (2025) pp. 112-113 (grain-size systematics; SD '
                  'peak Bc ~15 mT; igneous grains stressed -> higher/more '
                  'variable coercivity than grown crystals)',
        'note': 'primary magmatic (titano)magnetite; broad and grain-size '
                'dependent, from low-coercivity coarse PSD-MD grains to finer '
                'PSD/SD grains; oxidation to titanomaghemite raises coercivity '
                '(see maghemite_oxidized)'},
    'magnetite_eolian': {
        'B_median_mT': (18.0, 45.0), 'dp': (0.20, 0.40),
        'skew': (-5.0, 0.0),
        'source': 'Egli (2004a) component ED (aeolian dust; MDF ~28 mT); '
                  'Roberts (2025) does not give an eolian-specific value',
        'note': 'aeolian / loess detrital magnetite (often partly '
                'maghemitized)'},
    'magnetite_biogenic_soft': {
        'B_median_mT': (25.0, 55.0), 'dp': (0.10, 0.25),
        'skew': (-5.0, 0.0),
        'source': 'Egli (2004a) component BS (MDF ~45 mT, DP ~0.17); '
                  'Roberts (2025) pp. 119-121',
        'note': 'biogenic soft magnetite (equant magnetosomes); diagnostic '
                'narrow DP (~0.1-0.2)'},
    'magnetite_biogenic_hard': {
        'B_median_mT': (50.0, 100.0), 'dp': (0.08, 0.22),
        'skew': (-5.0, 0.0),
        'source': 'Egli (2004a) component BH (MDF ~73 mT, DP ~0.11); '
                  'Roberts (2025) pp. 119-121',
        'note': 'biogenic hard magnetite (elongated magnetosome chains); '
                'diagnostic very narrow DP'},
    'magnetite': {
        'B_median_mT': (8.0, 100.0), 'dp': (0.15, 0.50),
        'skew': (-5.0, 0.0),
        'source': 'generic magnetite window spanning the specific entries '
                  '(coarse soft ~10 mT to fine/oxidized hard ~100 mT); '
                  'Egli (2004a); Dunlop (1986, '
                  'doi:10.1016/0012-821X(86)90068-3) measured submicron '
                  'magnetite backfield Bcr ~27-50 mT and IRM-acquisition '
                  'medians ~39-68 mT (0.22 um PSD to SD), finer grains harder '
                  'but with narrower spectra; Roberts (2025) pp. 105-141',
        'note': 'broad default for stoichiometric-to-partly-oxidized '
                'magnetite when the grain population is unknown; left-skewed. '
                'Use the specific entries (detrital, biogenic, ...) when the '
                'population is known, or maghemite_oxidized for a distinctly '
                'harder (surface-oxidized) magnetite'},
    'maghemite': {
        'B_median_mT': (10.0, 40.0), 'dp': (0.15, 0.35),
        'skew': (-5.0, 0.5),
        'source': 'Roberts (2025) pp. 300-301 (pure gamma-Fe2O3: modal '
                  'coercivity ~14 mT equant to ~34 mT elongated; saturates '
                  '<100-200 mT)',
        'note': 'pure maghemite is SOFT, softer than magnetite; skewed '
                'distributions with a high-field tail. Distinct from the '
                'harder oxidized-magnetite phase (maghemite_oxidized)'},
    'maghemite_oxidized': {
        'B_median_mT': (45.0, 90.0), 'dp': (0.15, 0.35),
        'skew': (-5.0, 0.0),
        'source': 'Roberts (2025) pp. 300-301 (surface-maghemitized magnetite '
                  'Bcr ~52 mT, harder than either endmember; harder in '
                  'coarser grains); Egli (2004a) loess component L',
        'note': 'low-temperature (surface) oxidized magnetite (core-shell); '
                'HARDER than either pure magnetite or pure maghemite'},
    'greigite': {
        'B_median_mT': (25.0, 95.0), 'dp': (0.15, 0.35),
        'skew': (-3.0, 1.0),
        'source': 'Roberts (2025) pp. 401, 405-406 (SD Bcr ~75 mT [60-95], '
                  'SD+MD ~45 mT, MD ~24.5 mT; saturates <0.3 T)',
        'note': 'authigenic ferrimagnetic iron sulphide; SD SFD near-'
                'symmetric and narrow, left-skewed when SP/MD present; '
                'overlaps magnetite (both saturate <0.3 T)'},
    'pyrrhotite': {
        'B_median_mT': (25.0, 200.0), 'dp': (0.20, 0.50),
        'skew': (-1.0, 5.0),
        'source': 'Roberts (2025) pp. 369, 373-374, 383 (4C: Bc 16-70 mT by '
                  'grain size; FORC peaks ~30 mT MD to ~75-125 mT fine SD; '
                  'metamorphic/3C to >300-400 mT; needs >2 T to saturate)',
        'note': 'monoclinic 4C (+3C) pyrrhotite; medium- to high-coercivity, '
                'strongly grain-size/polytype dependent, right-skewed (hard '
                'tail); backfield under-samples the hard fraction, so '
                'contributions are minimum estimates'},
    'hematite_pigmentary': {
        'B_median_mT': (150.0, 800.0), 'dp': (0.35, 0.95),
        'skew': (-2.0, 4.0),
        'source': 'Ozdemir & Dunlop (2014, JGR 119, 2582-2594, '
                  'doi:10.1002/2013JB010739): fine (~100s nm) SD hematite, '
                  'Hc ~150-350 mT for 0.12-0.45 um and up to ~670 mT near '
                  '0.1 um, Hcr/Hc ~1.45-1.62 -> Bcr ~220 mT to ~1 T; '
                  'Roberts (2025) pp. 190, 197, 224; Maxbauer et al. (2016) '
                  'red-bed pigmentary hematite (often fit skew-right)',
        'note': 'fine pigmentary/authigenic hematite (~100s of nm); intrinsic '
                'coercivity is high (fine SD) but the natural population is '
                'broad and often SP-affected, so the bulk median is variable '
                'and often lower; commonly skew-right; non-saturating in '
                'ordinary fields, so the median is a lower bound'},
    'hematite_detrital': {
        'B_median_mT': (400.0, 1500.0), 'dp': (0.18, 0.40),
        'skew': (-2.0, 3.0),
        'source': 'Ozdemir & Dunlop (2014, doi:10.1002/2013JB010739): '
                  'Hc ~ d^-0.61 over the fitting-relevant ~100s nm - 100s um '
                  'range, so fine specular is hard (several 100 mT to ~1 T) '
                  'and coarser specular softer (down to ~100-200 mT); '
                  'Roberts (2025) pp. 197, 224 (stable-SD, narrow, high '
                  'unblocking 660-680 C); Swanson-Hysell et al. (2019)',
        'note': 'detrital / specular (specularite) hematite spanning ~100s '
                'of nm to ~100s of um; well-crystallized and narrower (lower '
                'dp) than pigmentary hematite, harder when finer. Coercivity '
                'is grain-size controlled (finer = harder), so a coarser '
                'specular population overlaps the pigmentary window'},
    'hematite': {
        'B_median_mT': (150.0, 1500.0), 'dp': (0.20, 0.90),
        'skew': (-2.0, 4.0),
        'source': 'Ozdemir & Dunlop (2014, doi:10.1002/2013JB010739): over '
                  'the fitting-relevant ~100s nm - 100s um range hematite Hc '
                  'varies continuously as ~d^-0.61 (fine SD hard, coarser '
                  'specular softer); Roberts (2025); Heslop (2015)',
        'note': 'generic hematite window spanning the pigmentary and '
                'specular/detrital natural populations (~100s of nm to ~100s '
                'of um); coercivity is grain-size controlled. Use the specific '
                'entries when the population is known'},
}


def mineral_priors(mineral_names, tighten=1.0, widen=1.0, field_max_mT=None,
                   overrides=None):
    """
    Build a Bayesian-unmixing prior dictionary from named mineral components.

    Converts a list of component names from COERCIVITY_COMPONENT_LIBRARY
    into the `priors` dictionary accepted by unmix_coercivity_bayes, with a
    mean-coercivity, dispersion, and skew window per component. The mean
    window constrains the component's mean coercivity directly (the
    skew-normal location is derived from the sampled dp and skew), so the
    window is meaningful whatever the fitted skew. Components are sorted by
    their central coercivity so the returned order matches the (low-to-high
    coercivity) component ordering of the fit.

    The library windows are broad starting points; real samples often need
    them adapted. Use `tighten` to narrow every window, `widen` to broaden
    every window, and `overrides` to replace specific windows outright when
    a mineral in your samples sits outside its library range (for example a
    harder, finer-grained magnetite, or a hematite whose low-coercivity
    shoulder starts below the library's detrital-hematite window). A typical
    workflow is to fit unconstrained first, see where the components land,
    and then set the windows accordingly.

    Because these are informative priors on an ill-posed decomposition, they
    should be treated as soft constraints; see the caveats in the
    COERCIVITY_COMPONENT_LIBRARY documentation.

    Parameters
    ----------
    mineral_names : list of str
        Component names, each a key of COERCIVITY_COMPONENT_LIBRARY (e.g.
        ['magnetite_detrital', 'hematite_pigmentary', 'hematite_detrital']).
    tighten : float
        Factor (>= 1) by which to narrow every window about its center; 1
        keeps the library width.
    widen : float
        Factor (>= 1) by which to broaden every window about its center; 1
        keeps the library width. tighten and widen compose (net width factor
        = widen / tighten).
    field_max_mT : float, optional
        Maximum applied field of the measurement (mT). Coercivity upper
        bounds are clipped to this value, so that components whose window
        extends past the measured field (e.g. hard hematite or pyrrhotite in
        a 1-2 T experiment) are not given prior support the data cannot
        constrain.
    overrides : dict, optional
        Per-mineral window replacements, mapping a mineral name to a dict
        with any of 'B_median_mT', 'dp', 'skew' as (low, high) tuples. The
        replacement window is used in place of the library value (before
        tighten/widen and field clipping are applied), letting you anchor to
        the library for most minerals while tuning the ones your samples
        require.

    Returns
    -------
    dict
        A priors dictionary with 'mean', 'dp', and 'skew' keys, each a list
        of (low, high) tuples in the order of increasing coercivity, suitable
        for `unmix_coercivity_bayes(..., priors=...)`. The 'mean' window
        constrains each component's MEAN coercivity (log10 mT) -- so a library
        window means what it says regardless of the component's skew. The
        chosen component names, in the same order, are returned under the
        'components' key.
    """
    if isinstance(mineral_names, str):
        mineral_names = [mineral_names]
    if tighten < 1:
        raise ValueError('tighten must be >= 1')
    if widen < 1:
        raise ValueError('widen must be >= 1')
    overrides = overrides or {}
    scale = widen / tighten  # > 1 broadens, < 1 narrows

    def _rescale(low, high):
        center = 0.5 * (low + high)
        half = 0.5 * (high - low) * scale
        return center - half, center + half

    entries = []
    for name in mineral_names:
        if name not in COERCIVITY_COMPONENT_LIBRARY:
            raise KeyError(
                f"unknown mineral component '{name}'; available: "
                f'{sorted(COERCIVITY_COMPONENT_LIBRARY)}')
        entry = {**COERCIVITY_COMPONENT_LIBRARY[name], **overrides.get(name, {})}
        b_low, b_high = _rescale(*entry['B_median_mT'])
        b_low = max(b_low, 1e-3)  # keep positive for log10
        if field_max_mT is not None:
            # clip the upper bound to the measured field, but refuse to clip a
            # window whose lower bound is already at or above it: that would
            # collapse the window to zero width and silently pin the component
            # at exactly log10(field_max_mT). Such a component sits entirely
            # beyond the measured field and cannot be constrained here.
            if b_low >= field_max_mT:
                raise ValueError(
                    f"component '{name}': its coercivity window starts at "
                    f"{b_low:g} mT, at or above the maximum applied field "
                    f"({field_max_mT:g} mT), so this experiment cannot "
                    f"constrain {name}. Remove it from the mineral list, "
                    f"widen the field range, or supply an override window.")
            b_high = min(b_high, field_max_mT)
        entries.append((name, np.sqrt(b_low * b_high),
                        (np.log10(b_low), np.log10(b_high)),
                        _rescale(*entry['dp']), _rescale(*entry['skew'])))
    entries.sort(key=lambda item: item[1])

    return {
        'components': [item[0] for item in entries],
        'mean': [item[2] for item in entries],
        'dp': [item[3] for item in entries],
        'skew': [item[4] for item in entries],
    }


def _format_mT_axis(ax):
    """Label a log10(B) axis with field values in mT."""
    from matplotlib.ticker import FuncFormatter

    def _fmt(value, _pos):
        field = 10 ** value
        return f'{field:g}' if field < 1000 else f'{field:.0f}'
    ax.xaxis.set_major_formatter(FuncFormatter(_fmt))


# mineral family (for grouping/colouring the prior library) inferred from the
# component name, and a colour per family
_COERCIVITY_FAMILY_COLORS = {
    'magnetite': '#1f77b4', 'maghemite': '#17becf', 'Fe-sulphide': '#2ca02c',
    'hematite': '#d62728', 'other': '#7f7f7f'}


def _coercivity_family(name):
    """Mineral family of a COERCIVITY_COMPONENT_LIBRARY component name."""
    if name.startswith('magnetite'):
        return 'magnetite'
    if name.startswith('maghemite'):
        return 'maghemite'
    if name in ('greigite', 'pyrrhotite'):
        return 'Fe-sulphide'
    if name.startswith('hematite'):
        return 'hematite'
    return 'other'


def coercivity_prior_table(minerals=None):
    """
    Summarize the coercivity-component prior library as a table.

    Parameters
    ----------
    minerals : list of str, optional
        Component names, each a key of COERCIVITY_COMPONENT_LIBRARY. Defaults
        to the whole library, ordered by central (geometric-mean) coercivity.

    Returns
    -------
    pandas.DataFrame
        One row per component with its family, mean-coercivity window (mT),
        dispersion window (dp, log10 units), skew (Azzalini alpha) window, the
        implied distribution asymmetry, and the leading literature source.
    """
    names = list(minerals) if minerals is not None \
        else list(COERCIVITY_COMPONENT_LIBRARY)
    rows = []
    for name in names:
        if name not in COERCIVITY_COMPONENT_LIBRARY:
            raise KeyError(f"unknown mineral component '{name}'")
        entry = COERCIVITY_COMPONENT_LIBRARY[name]
        b_lo, b_hi = entry['B_median_mT']
        sk_lo, sk_hi = entry['skew']
        sk_c = 0.5 * (sk_lo + sk_hi)
        asymmetry = ('left (low-field tail)' if sk_c < -0.3 else
                     'right (high-field tail)' if sk_c > 0.3 else
                     'near-symmetric')
        rows.append({
            'component': name,
            'family': _coercivity_family(name),
            'mean coercivity (mT)': f'{b_lo:g}-{b_hi:g}',
            'dp (log10)': f"{entry['dp'][0]:g}-{entry['dp'][1]:g}",
            'skew (alpha)': f'{sk_lo:g}-{sk_hi:g}',
            'asymmetry': asymmetry,
            'central coercivity (mT)': float(np.sqrt(b_lo * b_hi)),
            'source': entry['source'].split(';')[0],
        })
    table = pd.DataFrame(rows).sort_values('central coercivity (mT)')
    return table.reset_index(drop=True)


def plot_coercivity_prior_library(minerals=None, field_range=(1.0, 5e3),
                                  n_grid=400, figsize=None, ax=None):
    """
    Visualize the coercivity-component prior library.

    Draws, for each named mineral component, the skew-normal coercivity
    distribution implied by the centre of its library windows (mean
    coercivity, dispersion, and skew) as a ridgeline over a shared log field
    axis, with the mean-coercivity window drawn as a bar at the baseline and
    a dot at its centre. Components are coloured by mineral family and ordered
    by central coercivity, so the coercivity ranges of the different minerals,
    their characteristic widths and skews, and -- importantly -- their
    overlaps (the reason a coercivity prior constrains a window rather than
    identifying a mineral) are all legible at a glance.

    Parameters
    ----------
    minerals : list of str, optional
        Component names to show (default: the whole library).
    field_range : tuple
        (min, max) field in mT for the coercivity axis (default 1-5000).
    n_grid : int
        Number of points for the density curves.
    figsize : tuple, optional
        Figure size; a default is chosen from the number of components.
    ax : matplotlib.axes.Axes, optional
        Axis to draw on; a new figure is created if omitted.

    Returns
    -------
    tuple
        (fig, ax).
    """
    from matplotlib.patches import Patch
    names = list(minerals) if minerals is not None \
        else list(COERCIVITY_COMPONENT_LIBRARY)
    rows = []
    for name in names:
        entry = COERCIVITY_COMPONENT_LIBRARY[name]
        b_lo, b_hi = entry['B_median_mT']
        dp_c = 0.5 * (entry['dp'][0] + entry['dp'][1])
        sk_c = 0.5 * (entry['skew'][0] + entry['skew'][1])
        rows.append((name, b_lo, b_hi, float(np.sqrt(b_lo * b_hi)), dp_c,
                     sk_c, _coercivity_family(name)))
    rows.sort(key=lambda r: r[3])

    x_grid = np.linspace(np.log10(field_range[0]), np.log10(field_range[1]),
                         n_grid)
    if figsize is None:
        figsize = (8.5, 0.7 * len(rows) + 1.2)
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
    for i, (name, b_lo, b_hi, b_c, dp_c, sk_c, family) in enumerate(rows):
        color = _COERCIVITY_FAMILY_COLORS.get(family, 'grey')
        # representative shape: centre coercivity is the MEAN, so derive the
        # skew-normal location from the central dp and skew
        delta = sk_c / np.sqrt(1.0 + sk_c ** 2)
        loc = np.log10(b_c) - dp_c * delta * np.sqrt(2.0 / np.pi)
        density = skewnormal_pdf(x_grid, loc, dp_c, sk_c)
        density = density / density.max() * 0.85
        ax.fill_between(x_grid, i, i + density, color=color, alpha=0.5, lw=0)
        ax.plot(x_grid, i + density, color=color, lw=1)
        ax.plot([np.log10(b_lo), np.log10(b_hi)], [i, i], color=color,
                lw=3.5, solid_capstyle='butt')
        ax.plot(np.log10(b_c), i, 'o', color=color, ms=4, zorder=5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    _format_mT_axis(ax)
    decades = range(int(np.floor(np.log10(field_range[0]))),
                    int(np.ceil(np.log10(field_range[1]))) + 1)
    ax.set_xticks([d for d in decades])
    ax.set_xticks([np.log10(m * 10.0 ** d) for d in decades
                   for m in range(2, 10)], minor=True)
    ax.set_xlabel('coercivity (mT)')
    ax.set_xlim(np.log10(field_range[0]), np.log10(field_range[1]))
    ax.set_ylim(-0.6, len(rows) + 0.2)
    ax.grid(axis='x', alpha=0.25)
    families_present = [f for f in _COERCIVITY_FAMILY_COLORS
                        if any(r[6] == f for r in rows)]
    ax.legend(handles=[Patch(color=_COERCIVITY_FAMILY_COLORS[f], label=f)
                       for f in families_present],
              fontsize=8, loc='lower right', framealpha=0.9,
              title='mineral family')
    fig.tight_layout()
    return fig, ax


def _unmixing_component_colors(b_means_mT, color_by, class_boundaries,
                               class_colors):
    """Assign a color to each component, by fit order or coercivity class."""
    n = len(b_means_mT)
    if color_by == 'component':
        return [f'C{i}' for i in range(n)]
    if color_by not in ('class', 'coercivity'):
        raise ValueError("color_by must be 'component', 'class', or "
                         "'coercivity'")
    if class_boundaries is None:
        raise ValueError("class_boundaries is required when color_by='class'")
    boundaries = np.sort(np.atleast_1d(class_boundaries).astype(float))
    n_classes = len(boundaries) + 1
    if class_colors is None:
        class_colors = (['royalblue', 'crimson'] if n_classes == 2
                        else [plt.get_cmap('coolwarm')(t)
                              for t in np.linspace(0, 1, n_classes)])
    if len(class_colors) != n_classes:
        raise ValueError(f'class_colors must have {n_classes} entries '
                         f'({len(boundaries)} boundaries + 1)')
    # component in class k when its mean coercivity exceeds the k-th boundary;
    # a component exactly on a boundary is assigned to the lower class
    class_index = np.searchsorted(boundaries, np.asarray(b_means_mT),
                                  side='left')
    return [class_colors[k] for k in class_index]


def _result_is_spectrum(result):
    """
    Whether result['x']/result['y'] hold the coercivity spectrum rather than
    the measured curve, i.e. the fit was done in spectrum space. Plot helpers
    use this so they do not differentiate an already-differentiated spectrum.
    """
    method = result.get('method')
    if method in ('spectrum', 'maxunmix'):
        return True
    if method == 'bayes':
        return result.get('space') == 'spectrum'
    return False


def _result_spectrum(result):
    """Return (x_mid, spectrum) for a result, without double-differentiating a
    spectrum-space fit whose x/y are already the spectrum."""
    x, y = result['x'], result['y']
    if _result_is_spectrum(result):
        return x, y
    return coercivity_spectrum_from_curve(x, y, result['curve_type'])


def plot_coercivity_unmixing(result, show_components=True,
                             show_bootstrap=True, show_initial=False,
                             n_grid=300, figsize=None, title=None,
                             color_by='component', class_boundaries=None,
                             class_colors=None):
    """
    Plot an unmixing result in its fitted data space.

    For spectrum-space fits a single panel shows the data, total model, and
    components. For measurement-space (curve) fits an upper panel shows the
    measured curve with the cumulative model and a lower panel shows the
    finite-difference spectrum of the data with the implied component
    density curves. Bootstrap 95% bands are drawn when present.

    Parameters
    ----------
    result : dict
        Result from unmix_coercivity_spectrum, unmix_backfield_curve, or
        unmixing_bootstrap.
    show_components : bool
        Draw the individual components (default True).
    show_bootstrap : bool
        Draw bootstrap confidence bands if available (default True).
    show_initial : bool
        Also draw the model implied by the initial parameters (dotted),
        useful for judging how far the optimizer moved (default False).
    n_grid : int
        Number of points for smooth model curves.
    figsize : tuple, optional
        Figure size; defaults depend on the number of panels.
    title : str, optional
        Figure title.
    color_by : str
        How to color the components. 'component' (default) colors by fit
        order (C0, C1, ...). 'class' (or the alias 'coercivity') colors
        each component by the coercivity class its mean field falls into,
        so the mineralogy is read directly and a second component of the
        same mineral does not take a different color; requires
        class_boundaries.
    class_boundaries : float or sequence of float, optional
        Coercivity cut points in mT that partition the components into
        classes when color_by='class' (e.g. 200 for a magnetite/hematite
        split, or [30, 300] for three classes).
    class_colors : sequence, optional
        One color per class (length = number of boundaries + 1). Defaults
        to blue/red for two classes, or a diverging colormap otherwise.

    Returns
    -------
    tuple
        (fig, axes) with axes a list of the panel axes.
    """
    method = result['method']
    curve_type = result['curve_type']
    params = result['params']
    param_arr = params[UNMIX_PARAM_COLUMNS].to_numpy()
    x, y = result['x'], result['y']
    x_grid = np.linspace(x.min(), x.max(), n_grid)
    component_colors = _unmixing_component_colors(
        params['B_mean_mT'].to_numpy(), color_by, class_boundaries,
        class_colors)
    boot = None
    band_label = '95% bootstrap band'
    if show_bootstrap:
        if 'bootstrap' in result:
            boot = result['bootstrap']
        elif 'bayes' in result:
            boot = result['bayes']
            band_label = '95% credible band'

    plot_as_curve = (method in ('curve', 'bayes')
                     and result.get('space', 'curve') != 'spectrum')
    n_panels = 2 if plot_as_curve else 1
    if figsize is None:
        figsize = (8, 4.5 * n_panels)
    fig, axes = plt.subplots(nrows=n_panels, ncols=1, figsize=figsize,
                             sharex=True)
    axes = list(np.atleast_1d(axes))

    def _component_label(i):
        row = params.loc[i]
        return (f'component {i}: {row["B_mean_mT"]:.0f} mT, '
                f'DP {row["sd_log"]:.2f}, {row["proportion"] * 100:.0f}%')

    if plot_as_curve:
        ax_curve, ax_spec = axes
        ax_curve.scatter(x, y, c='grey', s=12, label='measurements')
        ax_curve.plot(x_grid, coercivity_curve_model(
            x_grid, param_arr, offset=result['offset'],
            curve_type=curve_type), c='k', label='model')
        if show_components:
            comps = coercivity_curve_components(x_grid, param_arr,
                                                curve_type=curve_type)
            for i in range(len(params)):
                ax_curve.plot(x_grid, comps[i] + result['offset'],
                              c=component_colors[i], alpha=0.8)
        if boot is not None:
            curves = boot['curves']
            ax_curve.fill_between(curves['x_grid'], curves['total_p2_5'],
                                  curves['total_p97_5'], color='k',
                                  alpha=0.2, label=band_label)
        ax_curve.set_ylabel('magnetization')
        ax_curve.legend(fontsize=9)
        # implied spectrum panel from finite differences of the data
        x_mid, spec = coercivity_spectrum_from_curve(x, y, curve_type)
        ax_spec.scatter(x_mid, spec, c='grey', s=12,
                        label='finite-difference spectrum')
        ax_spec.plot(x_grid, coercivity_spectrum_model(x_grid, param_arr),
                     c='k', label='model')
        if show_components:
            comps = coercivity_spectrum_components(x_grid, param_arr)
            for i, comp_index in enumerate(params.index):
                ax_spec.plot(x_grid, comps[i], c=component_colors[i],
                             label=_component_label(comp_index))
        if show_initial:
            init_arr = _unmix_parameters_to_array(
                result['initial_parameters'])
            ax_spec.plot(x_grid, coercivity_spectrum_model(x_grid, init_arr),
                         c='k', ls=':', alpha=0.6, label='initial model')
        ax_spec.set_ylabel('dM/dlog$_{10}$(B)')
        ax_spec.set_xlabel('field (mT)')
        ax_spec.legend(fontsize=9)
    else:
        ax_spec = axes[0]
        ax_spec.scatter(x, y, c='grey', s=12, label='coercivity spectrum')
        if boot is not None:
            curves = boot['curves']
            ax_spec.fill_between(curves['x_grid'], curves['total_p2_5'],
                                 curves['total_p97_5'], color='k', alpha=0.2,
                                 label=band_label)
            if show_components:
                for i in range(len(params)):
                    ax_spec.fill_between(curves['x_grid'],
                                         curves['components_p2_5'][i],
                                         curves['components_p97_5'][i],
                                         color=component_colors[i], alpha=0.2)
        ax_spec.plot(x_grid, coercivity_spectrum_model(x_grid, param_arr),
                     c='k', label='model')
        if show_components:
            comps = coercivity_spectrum_components(x_grid, param_arr)
            for i, comp_index in enumerate(params.index):
                ax_spec.plot(x_grid, comps[i], c=component_colors[i],
                             label=_component_label(comp_index))
        if show_initial:
            init_arr = _unmix_parameters_to_array(
                result['initial_parameters'])
            ax_spec.plot(x_grid, coercivity_spectrum_model(x_grid, init_arr),
                         c='k', ls=':', alpha=0.6, label='initial model')
        ax_spec.set_ylabel('dM/dlog$_{10}$(B)')
        ax_spec.set_xlabel('field (mT)')
        ax_spec.legend(fontsize=9)

    for ax in axes:
        _format_mT_axis(ax)
    if title is not None:
        fig.suptitle(title)
    fig.tight_layout()
    return fig, axes


def _unmixing_samples(result):
    """
    Return the per-draw parameter samples from a bootstrap or Bayesian result.

    Both unmixing_bootstrap and unmix_coercivity_bayes attach a dictionary of
    posterior/bootstrap draws (one array of shape (n_draws, n_components) per
    tracked quantity). This helper returns that dictionary along with a label
    describing the uncertainty source, or raises if the result carries no
    draws.

    Returns
    -------
    tuple
        (samples, source_label) where samples maps quantity name -> array of
        shape (n_draws, n_components) and source_label is 'bootstrap' or
        'posterior'.
    """
    if 'bayes' in result:
        return result['bayes']['samples'], 'posterior'
    if 'bootstrap' in result:
        return result['bootstrap']['param_samples'], 'bootstrap'
    raise ValueError('result has no bootstrap or Bayesian draws; run '
                     'unmixing_bootstrap or method="bayes" first')


def plot_unmixing_posterior(result, quantity='B_mean_mT', bins=40,
                            figsize=None, colors=None):
    """
    Plot marginal uncertainty distributions of a component quantity.

    Draws one histogram per component of the requested derived quantity from
    the bootstrap or Bayesian draws, with the median and 95% interval marked.
    This visualizes how tightly each component parameter is constrained,
    including asymmetric and multimodal uncertainties that a single
    standard-error value cannot convey.

    Parameters
    ----------
    result : dict
        Result from unmixing_bootstrap or unmix_coercivity_bayes.
    quantity : str
        Name of the quantity to plot (e.g. 'B_mean_mT', 'proportion',
        'sd_log', 'location', 'dp', 'skew'). Must be present in the draws.
    bins : int
        Number of histogram bins.
    figsize : tuple, optional
        Figure size; defaults to (7, 2.2 * n_components).
    colors : list, optional
        Per-component colors; defaults to the matplotlib C0, C1, ... cycle.

    Returns
    -------
    tuple
        (fig, axes).
    """
    samples, source = _unmixing_samples(result)
    if quantity not in samples:
        raise KeyError(f"'{quantity}' is not in the draws; available: "
                       f'{sorted(samples)}')
    values = np.asarray(samples[quantity])
    K = values.shape[1]
    log_x = quantity in ('B_mean_mT', 'B_median_mT', 'B_peak_mT')
    if figsize is None:
        figsize = (7, 2.2 * K)
    if colors is None:
        colors = [f'C{i}' for i in range(K)]
    fig, axes = plt.subplots(K, 1, figsize=figsize, squeeze=False)
    axes = axes.ravel()
    for i in range(K):
        column = values[:, i]
        median = np.median(column)
        low, high = np.percentile(column, [2.5, 97.5])
        if log_x:
            bin_edges = np.logspace(np.log10(column.min()),
                                    np.log10(column.max()), bins)
            axes[i].set_xscale('log')
        else:
            bin_edges = bins
        axes[i].hist(column, bins=bin_edges, color=colors[i], alpha=0.6,
                     density=True)
        axes[i].axvline(median, color='k', lw=1.2,
                        label=f'median {median:.3g}')
        axes[i].axvline(low, color='k', ls='--', lw=0.9)
        axes[i].axvline(high, color='k', ls='--', lw=0.9,
                        label=f'95%: [{low:.3g}, {high:.3g}]')
        axes[i].set_ylabel(f'component {i + 1}')
        axes[i].legend(fontsize=8)
    axes[-1].set_xlabel(f'{quantity} ({source} draws)')
    fig.tight_layout()
    return fig, axes


def plot_unmixing_tradeoff(result, x='B_mean_mT', y='proportion',
                           component=None, figsize=(5, 5), colors=None):
    """
    Scatter two component quantities across draws to reveal parameter trade-offs.

    Overlapping coercivity components trade parameters against one another;
    plotting one quantity against another across the bootstrap or posterior
    draws exposes these correlations (and any multimodality) that marginal
    intervals hide. By default every component is shown; pass a component
    index to isolate one.

    Parameters
    ----------
    result : dict
        Result from unmixing_bootstrap or unmix_coercivity_bayes.
    x, y : str
        Quantity names for the two axes (e.g. 'B_mean_mT', 'proportion',
        'sd_log').
    component : int, optional
        1-based component index to plot alone; if None, all components are
        overlaid.
    figsize : tuple
        Figure size.
    colors : list, optional
        Per-component colors.

    Returns
    -------
    tuple
        (fig, ax).
    """
    samples, source = _unmixing_samples(result)
    for name in (x, y):
        if name not in samples:
            raise KeyError(f"'{name}' is not in the draws; available: "
                           f'{sorted(samples)}')
    xv = np.asarray(samples[x])
    yv = np.asarray(samples[y])
    K = xv.shape[1]
    components = range(K) if component is None else [component - 1]
    if colors is None:
        colors = [f'C{i}' for i in range(K)]
    fig, ax = plt.subplots(figsize=figsize)
    for i in components:
        ax.scatter(xv[:, i], yv[:, i], s=6, alpha=0.25, color=colors[i],
                   edgecolors='none', label=f'component {i + 1}')
    if x in ('B_mean_mT', 'B_median_mT', 'B_peak_mT'):
        ax.set_xscale('log')
    if y in ('B_mean_mT', 'B_median_mT', 'B_peak_mT'):
        ax.set_yscale('log')
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f'parameter trade-off ({source} draws)')
    if component is None and K > 1:
        ax.legend(fontsize=8)
    fig.tight_layout()
    return fig, ax


def plot_unmixing_ensemble(result, space='spectrum', n_draws=200, n_grid=300,
                           show_components=True, figsize=(8, 5), title=None,
                           colors=None, random_seed=None):
    """
    Overlay many draws of the model curves to visualize decomposition spread.

    Rather than a single best fit with an error band, this draws the total
    model and (optionally) the individual components for many bootstrap or
    posterior samples, so the full range of decompositions consistent with
    the data is visible directly -- including cases where components exchange
    coercivity or amplitude between draws.

    Parameters
    ----------
    result : dict
        Result from unmixing_bootstrap or unmix_coercivity_bayes.
    space : str
        'spectrum' (dM/dlog10 B) or 'curve' (measurement space).
    n_draws : int
        Number of draws to overlay (capped at the number available).
    n_grid : int
        Number of field points for the smooth curves.
    show_components : bool
        Overlay per-component curves in addition to the total.
    figsize : tuple
        Figure size.
    title : str, optional
        Figure title.
    colors : list, optional
        Per-component colors.
    random_seed : None, int, or numpy.random.Generator
        Seed for choosing which draws to plot.

    Returns
    -------
    tuple
        (fig, ax).
    """
    assert space in ('spectrum', 'curve'), \
        "space must be 'spectrum' or 'curve'"
    samples, source = _unmixing_samples(result)
    rng = _resolve_rng(random_seed)
    curve_type = result['curve_type']
    x, y = result['x'], result['y']
    x_grid = np.linspace(x.min(), x.max(), n_grid)

    contribution = np.asarray(samples['contribution'])
    location = np.asarray(samples['location'])
    dp = np.asarray(samples['dp'])
    skew = np.asarray(samples['skew'])
    n_available, K = contribution.shape
    if colors is None:
        colors = [f'C{i}' for i in range(K)]
    offset_draws = np.asarray(result['bayes']['samples']['offset']) \
        if ('bayes' in result and space == 'curve') else None

    n_plot = min(n_draws, n_available)
    idx = rng.choice(n_available, size=n_plot, replace=False)

    fig, ax = plt.subplots(figsize=figsize)
    # data
    if space == 'spectrum':
        x_mid, spectrum = _result_spectrum(result)
        ax.scatter(x_mid, spectrum, s=10, c='grey', alpha=0.5, zorder=3,
                   label='data spectrum')
    else:
        ax.scatter(x, y, s=10, c='grey', alpha=0.5, zorder=3, label='data')

    for draw, j in enumerate(idx):
        params = np.column_stack([contribution[j], location[j], dp[j],
                                  skew[j]])
        if space == 'spectrum':
            total = coercivity_spectrum_model(x_grid, params)
            comps = (coercivity_spectrum_components(x_grid, params)
                     if show_components else None)
        else:
            offset = offset_draws[j] if offset_draws is not None \
                else result['offset']
            total = coercivity_curve_model(x_grid, params, offset=offset,
                                           curve_type=curve_type)
            comps = (coercivity_curve_components(x_grid, params,
                                                 curve_type=curve_type)
                     if show_components else None)
        ax.plot(x_grid, total, color='k', alpha=0.04, lw=0.8,
                label='model draws' if draw == 0 else None)
        if comps is not None:
            for i in range(K):
                ax.plot(x_grid, comps[i], color=colors[i], alpha=0.04,
                        lw=0.8,
                        label=f'component {i + 1}' if draw == 0 else None)
    ax.set_xlabel('field (mT)')
    ax.set_ylabel('dM/dlog$_{10}$(B)' if space == 'spectrum'
                  else 'magnetization')
    _format_mT_axis(ax)
    ax.set_title(title if title is not None
                 else f'ensemble of {n_plot} {source} draws')
    # legend with opaque proxies
    handles, labels = ax.get_legend_handles_labels()
    for handle in handles:
        handle.set_alpha(1.0)
    ax.legend(handles, labels, fontsize=8)
    fig.tight_layout()
    return fig, ax


def plot_multistart_solutions(result, max_solutions=6, space='spectrum',
                              n_grid=300, figsize=None, colors=None):
    """
    Visualize the distinct solutions found by a multi-start analysis.

    Produces a panel of small multiples, one per distinct solution (ordered
    by Akaike weight), each showing that solution's decomposition against the
    data, plus a final parameter-space map that places every solution's
    components on a coercivity-versus-proportion plot. Together these make
    the non-uniqueness of the decomposition concrete: how many genuinely
    different solutions the data admit, how each partitions the spectrum, and
    how much statistical support each carries.

    Parameters
    ----------
    result : dict
        Result from unmixing_multistart (carries a 'multistart' entry).
    max_solutions : int
        Maximum number of distinct solutions to draw as small multiples
        (the highest-weight solutions are shown).
    space : str
        'spectrum' (dM/dlog10 B) or 'curve' (measurement space) for the
        decomposition panels.
    n_grid : int
        Number of field points for the smooth model curves.
    figsize : tuple, optional
        Figure size; a default is chosen from the panel count.
    colors : list, optional
        Per-solution colors; defaults to the tab10 cycle.

    Returns
    -------
    tuple
        (fig, axes).
    """
    if 'multistart' not in result:
        raise ValueError('result has no multistart analysis; run '
                         'unmixing_multistart first')
    assert space in ('spectrum', 'curve'), \
        "space must be 'spectrum' or 'curve'"
    multistart = result['multistart']
    solutions = multistart['solutions']
    solution_results = multistart['results']
    curve_type = result['curve_type']
    x, y = result['x'], result['y']
    x_grid = np.linspace(x.min(), x.max(), n_grid)

    # order solutions by Akaike weight (descending)
    order = np.argsort(solutions['akaike_weight'].to_numpy())[::-1]
    n_show = min(max_solutions, len(order))
    order = order[:n_show]
    if colors is None:
        cmap = plt.get_cmap('tab10')
        colors = [cmap(i % 10) for i in range(len(solution_results))]

    n_panels = n_show + 1  # decompositions + parameter map
    n_cols = min(3, n_panels)
    n_rows = int(np.ceil(n_panels / n_cols))
    if figsize is None:
        figsize = (4.2 * n_cols, 3.2 * n_rows)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, squeeze=False)
    axes_flat = axes.ravel()

    if space == 'spectrum':
        x_data, y_data = _result_spectrum(result)
    else:
        x_data, y_data = x, y

    for panel, sol_idx in enumerate(order):
        ax = axes_flat[panel]
        fit = solution_results[sol_idx]
        params = fit['params'][UNMIX_PARAM_COLUMNS].to_numpy()
        weight = solutions['akaike_weight'].iloc[sol_idx]
        n_hits = int(solutions['n_hits'].iloc[sol_idx])
        ax.scatter(x_data, y_data, s=8, c='lightgrey', zorder=1)
        if space == 'spectrum':
            total = coercivity_spectrum_model(x_grid, params)
            comps = coercivity_spectrum_components(x_grid, params)
        else:
            total = coercivity_curve_model(x_grid, params,
                                           offset=fit.get('offset', 0.0),
                                           curve_type=curve_type)
            comps = coercivity_curve_components(x_grid, params,
                                                curve_type=curve_type)
        for i in range(len(params)):
            ax.plot(x_grid, comps[i], color=colors[sol_idx], lw=1.2,
                    alpha=0.9)
        ax.plot(x_grid, total, color='k', lw=1.2)
        ax.set_title(f'solution {sol_idx + 1}: weight {weight:.2f}, '
                     f'{n_hits} starts', fontsize=9,
                     color=colors[sol_idx])
        _format_mT_axis(ax)
        ax.set_xlabel('field (mT)', fontsize=8)
        ax.tick_params(labelsize=7)

    # parameter-space map panel
    ax_map = axes_flat[n_show]
    for sol_idx in order:
        row = solutions.iloc[sol_idx]
        weight = row['akaike_weight']
        component_cols = [c for c in solutions.columns
                          if c.startswith('B_mean_mT_c')]
        for col in component_cols:
            suffix = col.split('_c')[-1]
            proportion = row.get(f'proportion_c{suffix}', np.nan)
            ax_map.scatter(row[col], proportion, s=30 + 300 * weight,
                           color=colors[sol_idx], alpha=0.7,
                           edgecolors='k', linewidths=0.5)
    # x-data are already in mT (not log10 units), so a plain log scale is used
    ax_map.set_xscale('log')
    ax_map.set_xlabel('component mean coercivity (mT)', fontsize=8)
    ax_map.set_ylabel('proportion', fontsize=8)
    ax_map.set_title('solution map (size = Akaike weight)', fontsize=9)
    ax_map.tick_params(labelsize=7)

    for ax in axes_flat[n_panels:]:
        ax.axis('off')
    fig.tight_layout()
    return fig, axes_flat[:n_panels]


def interactive_coercivity_unmixing(x, magnetization, n_components=2,
                                    method='spectrum',
                                    curve_type='backfield', vary_skew=True,
                                    figsize=(9, 5)):
    """
    Interactive widget for choosing initial unmixing parameters visually.

    Initial parameter choices strongly influence nonlinear unmixing fits.
    This widget shows the coercivity spectrum with a live model built from
    per-component sliders (peak field in mT on a log scale, proportion of
    the total remanence, dispersion DP, and skew). Sliders are seeded from
    automatic peak detection. Pressing "Fit" runs the chosen optimizer
    (spectrum- or measurement-space) starting from the current slider
    values and overlays the optimized model.

    *Important*: run `%matplotlib widget` in the notebook first so the
    figure updates live.

    Parameters
    ----------
    x : array-like
        log10 of field values (mT), e.g. 'log_dc_field' from
        backfield_data_processing.
    magnetization : array-like
        Remanence curve values at x (e.g. 'magn_mass_shift').
    n_components : int
        Number of components (default 2).
    method : str
        'spectrum' or 'curve' -- the fitting approach used by the Fit
        button.
    curve_type : str
        'backfield' or 'acquisition'.
    vary_skew : bool
        Include skew sliders and let the fit vary skew (default True).
    figsize : tuple
        Figure size.

    Returns
    -------
    dict
        A live handle with keys 'initial_parameters' (DataFrame updated as
        sliders move; pass to the unmixing functions) and 'result' (filled
        with the standardized result dictionary after Fit is pressed).
    """
    _check_ipywidgets()
    assert method in ('spectrum', 'curve'), \
        "method must be 'spectrum' or 'curve'"
    x = np.asarray(x, dtype=float)
    M = np.asarray(magnetization, dtype=float)
    x_mid, spectrum = coercivity_spectrum_from_curve(x, M, curve_type)
    total_area = _trapz(spectrum, x_mid)
    x_grid = np.linspace(x.min(), x.max(), 300)

    auto = estimate_coercivity_components(x_mid, spectrum, n_components)
    handle = {'initial_parameters': None, 'result': None}

    fig, ax = plt.subplots(figsize=figsize)
    fig.canvas.header_visible = False

    sliders = []
    for i in range(n_components):
        peak_mT = 10 ** auto['location'][i]
        proportion_0 = min(auto['contribution'][i] / total_area, 1.0)
        column = [
            widgets.FloatLogSlider(value=peak_mT, base=10,
                                   min=x.min(), max=x.max(), step=0.01,
                                   description=f'B{i + 1} (mT)',
                                   continuous_update=False),
            widgets.FloatSlider(value=round(proportion_0, 2), min=0.0,
                                max=1.0, step=0.01,
                                description=f'proportion{i + 1}',
                                continuous_update=False),
            widgets.FloatSlider(value=round(auto['dp'][i], 2), min=0.02,
                                max=1.2, step=0.01,
                                description=f'DP{i + 1}',
                                continuous_update=False),
        ]
        if vary_skew:
            column.append(widgets.FloatSlider(value=0.0, min=-8.0, max=8.0,
                                              step=0.1,
                                              description=f'skew{i + 1}',
                                              continuous_update=False))
        sliders.append(column)

    fit_button = widgets.Button(description='Fit from these values',
                                button_style='primary')
    output = Output()

    def slider_parameters():
        rows = []
        for column in sliders:
            rows.append({
                'contribution': column[1].value * total_area,
                'location': np.log10(column[0].value),
                'dp': column[2].value,
                'skew': column[3].value if vary_skew else 0.0,
            })
        return pd.DataFrame(rows)

    def redraw(*_args):
        parameters = slider_parameters()
        handle['initial_parameters'] = parameters
        ax.clear()
        ax.scatter(x_mid, spectrum, c='grey', s=10, alpha=0.6,
                   label='coercivity spectrum')
        arr = parameters[UNMIX_PARAM_COLUMNS].to_numpy()
        comps = coercivity_spectrum_components(x_grid, arr)
        for i in range(n_components):
            ax.plot(x_grid, comps[i], c=f'C{i}', ls='--', alpha=0.8,
                    label=f'component {i + 1}')
        ax.plot(x_grid, comps.sum(axis=0), c='k', ls='--', alpha=0.8,
                label='total (manual)')
        if handle['result'] is not None:
            fitted = handle['result']['params'][UNMIX_PARAM_COLUMNS].to_numpy()
            fitted_comps = coercivity_spectrum_components(x_grid, fitted)
            for i in range(n_components):
                ax.plot(x_grid, fitted_comps[i], c=f'C{i}')
            ax.plot(x_grid, fitted_comps.sum(axis=0), c='k',
                    label='total (fitted)')
        ax.set_xlabel('field (mT)')
        ax.set_ylabel('dM/dlog$_{10}$(B)')
        _format_mT_axis(ax)
        ax.legend(fontsize=8)
        fig.canvas.draw_idle()

    def run_fit(_button):
        parameters = slider_parameters()
        with output:
            output.clear_output()
            try:
                if method == 'spectrum':
                    handle['result'] = unmix_coercivity_spectrum(
                        x_mid, spectrum, initial_parameters=parameters,
                        vary_skew=vary_skew)
                else:
                    handle['result'] = unmix_backfield_curve(
                        x, M, initial_parameters=parameters,
                        curve_type=curve_type, vary_skew=vary_skew)
            except (ValueError, RuntimeError) as error:
                print(f'fit failed: {error}')
                return
            stats = handle['result']['stats']
            print(f"fit success: {handle['result']['success']}, "
                  f"R^2 = {stats['r_squared']:.5f}, "
                  f"AIC = {stats['aic']:.1f}, BIC = {stats['bic']:.1f}")
            display(handle['result']['params'].round(4))
        redraw()

    for column in sliders:
        for slider in column:
            slider.observe(redraw, names='value')
    fit_button.on_click(run_fit)

    display(HBox([VBox(column) for column in sliders]))
    display(fit_button)
    display(output)
    redraw()
    return handle


def unmix_backfield_experiments(measurements, experiments=None,
                                n_components=2, method='spectrum',
                                initial_parameters=None, vary_skew=True,
                                n_boot=0, resample='cases',
                                proportion=1.0, noise_level=None,
                                smooth_mode='spline', smooth_frac=0.0,
                                drop_first=False, field='treat_dc_field',
                                magnetization='magn_mass', random_seed=None,
                                verbose=True, **method_kwargs):
    """
    Batch coercivity unmixing of backfield experiments in a MagIC
    measurements table.

    Each experiment is processed with backfield_data_processing and unmixed
    with the requested method (any name registered in UNMIXING_METHODS,
    dispatched through unmix_coercivity). When initial parameters are not
    supplied they are estimated automatically per experiment; supplying a
    common initial-parameter table (or a per-experiment dict, e.g. built
    with interactive_coercivity_unmixing) enforces a consistent starting
    model across specimens, which aids comparability of the resulting
    components.

    Parameters
    ----------
    measurements : pandas.DataFrame
        MagIC measurements table (must include 'experiment', 'specimen',
        'method_codes', and the field/magnetization columns).
    experiments : list, optional
        Experiment names to process. Defaults to all experiments whose
        method_codes include 'LP-BCR-BF'.
    n_components : int
        Number of components fit to each experiment (default 2).
    method : str
        Registered unmixing method name: 'spectrum', 'curve', 'maxunmix',
        or a custom method added with register_unmixing_method.
    initial_parameters : pandas.DataFrame or dict, optional
        Either a single initial-parameter table applied to every
        experiment, or a dict mapping experiment name -> table. Experiments
        missing from the dict fall back to automatic estimation.
    vary_skew : bool
        Whether skew parameters vary during fitting.
    n_boot : int
        If > 0, ensure each result carries a bootstrap with this many
        replicates (methods that bootstrap internally, like 'maxunmix',
        are not re-bootstrapped).
    resample, proportion, noise_level : see unmixing_bootstrap.
    smooth_mode, smooth_frac, drop_first : see backfield_data_processing.
        The defaults (spline with smooth_frac=0) leave the data unsmoothed.
    field, magnetization : str
        Column names in the measurements table.
    random_seed : None, int, or numpy.random.Generator
        Seed for reproducible bootstraps.
    verbose : bool
        Print progress and failures.
    **method_kwargs
        Additional keyword arguments passed to the unmixing method.

    Returns
    -------
    tuple
        (components_df, results) where components_df is a tidy DataFrame
        with one row per experiment and component (parameters, derived
        coercivities, uncertainties, fit statistics, and Bcr) and results
        is a dict mapping experiment name -> full result dictionary.
    """
    if method not in UNMIXING_METHODS:
        raise ValueError(f"unknown unmixing method '{method}'; available: "
                         f'{sorted(UNMIXING_METHODS)}')
    if experiments is None:
        is_backfield = measurements['method_codes'].astype(str).str.contains(
            'LP-BCR-BF', na=False)
        experiments = list(pd.unique(
            measurements.loc[is_backfield, 'experiment']))
    if len(experiments) == 0:
        raise ValueError('no backfield experiments found')
    rng = _resolve_rng(random_seed)

    results = {}
    rows = []
    failures = []
    for experiment_name in experiments:
        experiment = measurements[
            measurements['experiment'] == experiment_name].copy()
        if len(experiment) == 0:
            failures.append((experiment_name, 'experiment not found'))
            continue
        specimen = (experiment['specimen'].iloc[0]
                    if 'specimen' in experiment.columns else '')
        try:
            processed, Bcr = backfield_data_processing(
                experiment, field=field, magnetization=magnetization,
                smooth_mode=smooth_mode, smooth_frac=smooth_frac,
                drop_first=drop_first)
            x = processed['log_dc_field'].to_numpy()
            M = processed['magn_mass_shift'].to_numpy()
            if smooth_frac > 0:
                x_s = processed['smoothed_log_dc_field'].to_numpy()
                M_s = processed['smoothed_magn_mass_shift'].to_numpy()
            else:
                x_s, M_s = x, M

            if isinstance(initial_parameters, dict):
                initial = initial_parameters.get(experiment_name)
            else:
                initial = initial_parameters
            if initial is not None:
                initial = initial.copy()

            # The finite-difference least-squares methods ('spectrum',
            # 'maxunmix') fit the optionally smoothed curve, because
            # differentiating the raw curve amplifies its noise. The
            # measurement-space ('curve') and Bayesian methods fit the
            # unsmoothed data so their noise models -- the Bayesian methods
            # infer an explicit noise level -- see the true measurement noise;
            # feeding them the denoised curve would understate the noise and
            # yield overconfident credible intervals. (A Bayesian fit with
            # space='spectrum' differentiates the curve it is given
            # internally, so it too must receive the unsmoothed data.)
            x_fit, M_fit = ((x_s, M_s) if method in ('spectrum', 'maxunmix')
                            else (x, M))
            if method == 'maxunmix':
                method_kwargs.setdefault('n_boot', n_boot if n_boot > 0
                                         else 100)
                method_kwargs.setdefault('random_seed', rng)
            result = unmix_coercivity(
                x_fit, M_fit, method=method, n_components=n_components,
                initial_parameters=initial, vary_skew=vary_skew,
                **method_kwargs)
            if n_boot > 0 and 'bootstrap' not in result and 'bayes' not in result:
                result = unmixing_bootstrap(
                    result, n_boot=n_boot, resample=resample,
                    proportion=proportion, noise_level=noise_level,
                    random_seed=rng)
        except (ValueError, RuntimeError, KeyError) as error:
            failures.append((experiment_name, str(error)))
            if verbose:
                print(f'  {experiment_name}: FAILED ({error})')
            continue

        results[experiment_name] = result
        stats = result['stats']
        for comp_index, prow in result['params'].iterrows():
            row = {
                'experiment': experiment_name,
                'specimen': specimen,
                'method': method,
                'n_components': n_components,
                'component': comp_index,
                'success': result['success'],
                'Bcr_mT': Bcr * 1e3 if np.isfinite(Bcr) else np.nan,
                'rss': stats['rss'],
                'r_squared': stats['r_squared'],
                'aic': stats['aic'],
                'bic': stats['bic'],
            }
            row.update(prow.to_dict())
            uncertainty = result.get('bootstrap') or result.get('bayes')
            if uncertainty is not None:
                summary_row = uncertainty['param_summary'].loc[comp_index]
                for name in ['proportion', 'B_mean_mT', 'sd_log']:
                    row[f'{name}_std'] = summary_row[f'{name}_std']
                    row[f'{name}_p2_5'] = summary_row[f'{name}_p2_5']
                    row[f'{name}_p97_5'] = summary_row[f'{name}_p97_5']
            rows.append(row)
        if verbose:
            summary = ', '.join(
                f"{prow['B_mean_mT']:.0f} mT ({prow['proportion'] * 100:.0f}%)"
                for _i, prow in result['params'].iterrows())
            print(f'  {experiment_name} ({specimen}): {summary}, '
                  f"R^2 = {stats['r_squared']:.4f}")

    components_df = pd.DataFrame(rows)
    if verbose and failures:
        print(f'{len(failures)} experiment(s) failed: '
              f'{[name for name, _reason in failures]}')
    return components_df, results


def aggregate_by_class(components, boundaries_mT, class_names=None,
                       coercivity_column='B_mean_mT',
                       proportion_column='proportion',
                       contribution_column='contribution',
                       curve_factor=2.0, group_column='experiment',
                       passthrough=('specimen', 'Bcr_mT', 'r_squared')):
    """
    Aggregate fitted unmixing components into coercivity classes.

    Sums each component's remanence proportion (and, if available, its
    contribution) into classes defined by one or more coercivity cut points,
    per experiment. This is the robust way to quantify a mineral assemblage
    from an unmixing fit: because it integrates the fitted distribution
    within coercivity bands, the result is insensitive to how many
    components the optimizer used or how it split a single mineral, so long
    as the mineral populations are separated by the cut points. Typical use
    is a magnetite/hematite split at a single boundary, but any number of
    classes is supported.

    Parameters
    ----------
    components : pandas.DataFrame
        Tidy component table, e.g. from unmix_backfield_experiments (one row
        per experiment and component).
    boundaries_mT : float or sequence of float
        Coercivity cut point(s) in mT. A single value gives two classes; a
        sequence of k values gives k+1 classes. A component is placed in the
        class between the cut points that bracket its coercivity; a component
        exactly on a boundary goes to the lower class.
    class_names : sequence of str, optional
        Names for the classes, in order of increasing coercivity (length =
        number of boundaries + 1). Defaults to 'class_1', 'class_2', ...;
        for a two-class split you would typically pass e.g.
        ['magnetite', 'hematite'].
    coercivity_column : str
        Column used to classify each component (default 'B_mean_mT').
    proportion_column : str
        Column summed to give each class's remanence fraction (default
        'proportion').
    contribution_column : str
        Column summed (and divided by curve_factor) to give each class's
        absolute remanence; skipped if the column is absent.
    curve_factor : float
        Divisor applied to summed contributions. Use 2 for a shift-corrected
        backfield curve (which spans twice the saturation remanence) and 1
        for an IRM acquisition curve.
    group_column : str
        Column identifying each specimen/experiment to aggregate within
        (default 'experiment').
    passthrough : sequence of str
        Columns copied through unchanged (first value per group), e.g.
        specimen name and fit statistics. Missing columns are ignored.

    Returns
    -------
    pandas.DataFrame
        One row per group with the passthrough columns and, for each class,
        a '{name}_fraction' column and (when contributions are present) a
        '{name}_remanence' column.
    """
    if coercivity_column not in components.columns:
        raise KeyError(f"components has no '{coercivity_column}' column")
    boundaries = np.sort(np.atleast_1d(boundaries_mT).astype(float))
    edges = np.concatenate([[-np.inf], boundaries, [np.inf]])
    n_classes = len(edges) - 1
    if class_names is None:
        class_names = [f'class_{i + 1}' for i in range(n_classes)]
    if len(class_names) != n_classes:
        raise ValueError(f'class_names must have {n_classes} entries '
                         f'({len(boundaries)} boundaries + 1)')
    has_contribution = contribution_column in components.columns

    rows = []
    for group_name, group in components.groupby(group_column):
        row = {group_column: group_name}
        for col in passthrough:
            if col in group.columns:
                row[col] = group[col].iloc[0]
        b = group[coercivity_column].to_numpy()
        for k, name in enumerate(class_names):
            in_class = (b > edges[k]) & (b <= edges[k + 1])
            row[f'{name}_fraction'] = \
                group.loc[in_class, proportion_column].sum()
            if has_contribution:
                row[f'{name}_remanence'] = \
                    group.loc[in_class, contribution_column].sum() / curve_factor
        rows.append(row)
    return pd.DataFrame(rows)


def parse_specimen_description(description):
    """
    Parse a MagIC specimens 'description' cell into (text, dict).

    The description convention used here stores free text and a
    machine-readable JSON dictionary separated by ' | '. Legacy cells that
    contain a Python dict repr (from older rockmagpy versions) are parsed
    with ast.literal_eval.

    Parameters
    ----------
    description : str or NaN
        Contents of the description cell.

    Returns
    -------
    tuple
        (text, data) where text is the free-text portion (str, possibly
        empty) and data is the parsed dictionary (possibly empty).
    """
    if description is None or (isinstance(description, float)
                               and np.isnan(description)):
        return '', {}
    description = str(description).strip()
    if not description:
        return '', {}
    text, data = description, {}
    if ' | ' in description:
        candidate_text, candidate_json = description.split(' | ', 1)
        try:
            data = json.loads(candidate_json)
            return candidate_text, data
        except (json.JSONDecodeError, ValueError):
            pass
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(description)
            if isinstance(parsed, dict):
                return '', parsed
        except (ValueError, SyntaxError):
            continue
    return text, data


def _unmixing_component_record(row):
    """Build the JSON-serializable record for one unmixing component row."""
    record = {
        'component': int(row['component']),
        'B_mean_mT': round(float(row['B_mean_mT']), 2),
        'B_median_mT': round(float(row['B_median_mT']), 2),
        'DP': round(float(row['sd_log']), 4),
        'skew': round(float(row['skew']), 4),
        'proportion': round(float(row['proportion']), 4),
        'contribution': float(row['contribution']),
    }
    if 'B_mean_mT_p2_5' in row.index and pd.notna(row['B_mean_mT_p2_5']):
        record['B_mean_mT_95CI'] = [round(float(row['B_mean_mT_p2_5']), 2),
                                    round(float(row['B_mean_mT_p97_5']), 2)]
        record['proportion_95CI'] = [round(float(row['proportion_p2_5']), 4),
                                     round(float(row['proportion_p97_5']), 4)]
    return record


# Marker written into (and matched from) the JSON 'description' of specimens
# rows that unmixing_to_specimens_table(mode='rows') creates, so a re-run
# removes exactly its own previous component rows -- and never an original
# specimen row that merely carries a mode='description' payload or a rem_cmf.
_UNMIXING_ROW_MARKER = 'coercivity_unmixing_component_row'


def _match_specimen_rows(specimens_df, experiment_name, specimen_name):
    """Boolean mask of specimens rows matching an experiment (or specimen)."""
    if 'experiments' in specimens_df.columns:
        mask = specimens_df['experiments'].astype(str).str.contains(
            str(experiment_name), na=False, regex=False)
    else:
        mask = pd.Series(False, index=specimens_df.index)
    if not mask.any() and 'specimen' in specimens_df.columns:
        mask = specimens_df['specimen'] == specimen_name
    return mask


def unmixing_to_specimens_table(specimens_df, components_df, mode='rows'):
    """
    Record coercivity unmixing results in a MagIC specimens table.

    Two recording conventions are supported:

    - mode='rows' (default, conformant with the MagIC data model): one new
      specimens row is appended per experiment and component, populating
      the controlled-vocabulary columns rem_cmf (component median field,
      in tesla), rem_cd (component dispersion, log10 units), and
      rem_n_comp (number of components in the model), along with specimen
      identity columns copied from the matching existing row. The full
      parameter set (proportion, skew, confidence intervals, ...) is
      stored as JSON in each new row's 'description' cell. Rows from a
      previous call for the same experiments are replaced.
    - mode='description': the matching existing specimens rows are updated
      in place, storing the complete unmixing model as JSON under the
      'coercivity_unmixing' key in 'description' (any existing free text
      is preserved with a 'text | json' convention readable by
      parse_specimen_description).

    Parameters
    ----------
    specimens_df : pandas.DataFrame
        MagIC specimens table.
    components_df : pandas.DataFrame
        Tidy components table from unmix_backfield_experiments.
    mode : str
        'rows' or 'description'.

    Returns
    -------
    pandas.DataFrame
        The updated specimens table. With mode='description' the input
        table is also modified in place; with mode='rows' a new table is
        returned (pandas cannot append rows in place).
    """
    assert mode in ('rows', 'description'), \
        "mode must be 'rows' or 'description'"
    if 'description' not in specimens_df.columns:
        specimens_df['description'] = np.nan
    specimens_df['description'] = specimens_df['description'].astype(object)

    if mode == 'description':
        for experiment_name, group in components_df.groupby('experiment'):
            first = group.iloc[0]
            unmix_record = {
                'method': f"rockmagpy_{first['method']}",
                'software_version': pmagpy_version,
                'n_components': int(first['n_components']),
                'r_squared': round(float(first['r_squared']), 5),
                'components': [_unmixing_component_record(row)
                               for _i, row in group.iterrows()],
            }
            mask = _match_specimen_rows(specimens_df, experiment_name,
                                        first['specimen'])
            for idx in specimens_df.index[mask]:
                text, data = parse_specimen_description(
                    specimens_df.at[idx, 'description'])
                data['coercivity_unmixing'] = unmix_record
                payload = json.dumps(data)
                specimens_df.at[idx, 'description'] = (
                    f'{text} | {payload}' if text else payload)
        return specimens_df

    # mode == 'rows': one MagIC specimens row per component.
    # 'experiments' is deliberately NOT copied from the template: the template
    # row may list several experiments (colon-delimited), but a component
    # result derives from just this backfield experiment, so each new row's
    # 'experiments' is set to the single experiment_name below. Copying the
    # full colon-delimited string instead would also break the exact-match
    # cleanup, causing rows to accumulate on re-runs.
    identity_columns = ['specimen', 'sample', 'citations',
                        'result_quality', 'weight', 'volume']
    new_rows = []
    processed_experiments = []
    for experiment_name, group in components_df.groupby('experiment'):
        first = group.iloc[0]
        mask = _match_specimen_rows(specimens_df, experiment_name,
                                    first['specimen'])
        template = (specimens_df.loc[mask].iloc[0]
                    if mask.any() else pd.Series(dtype=object))
        processed_experiments.append(str(experiment_name))
        for _i, row in group.iterrows():
            new_row = {col: template[col] for col in identity_columns
                       if col in template.index and pd.notna(template[col])}
            new_row.setdefault('specimen', first['specimen'])
            new_row.setdefault('experiments', str(experiment_name))
            new_row['method_codes'] = 'LP-BCR-BF'
            new_row['software_packages'] = pmagpy_version
            new_row['rem_cmf'] = float(row['B_median_mT']) * 1e-3  # tesla
            new_row['rem_cd'] = float(row['sd_log'])
            new_row['rem_n_comp'] = int(row['n_components'])
            if pd.notna(row.get('Bcr_mT')):
                new_row['rem_bcr'] = float(row['Bcr_mT']) * 1e-3  # tesla
            record = {'coercivity_unmixing': {
                'method': f"rockmagpy_{row['method']}",
                'software_version': pmagpy_version,
                'experiment': str(experiment_name),
                'record_type': _UNMIXING_ROW_MARKER,
                'n_components': int(row['n_components']),
                'r_squared': round(float(row['r_squared']), 5),
                'component': _unmixing_component_record(row),
            }}
            new_row['description'] = json.dumps(record)
            new_rows.append(new_row)

    # Drop only the component rows a PREVIOUS mode='rows' call created for these
    # experiments. Rows are identified by the explicit marker this function
    # writes, never by a generic 'coercivity_unmixing' string or a populated
    # rem_cmf -- so an original specimen row carrying a mode='description'
    # payload (or an independently populated rem_cmf) is never removed.
    is_previous = specimens_df['description'].astype(str).str.contains(
        _UNMIXING_ROW_MARKER, na=False, regex=False)
    if 'experiments' in specimens_df.columns:
        processed_set = set(processed_experiments)
        # split on ':' so a row is matched whether its 'experiments' cell holds
        # the single experiment_name (as newly written) or a colon-delimited
        # list (e.g. a legacy row from before this fix), without the substring
        # false positives a plain str.contains would introduce
        in_processed = specimens_df['experiments'].apply(
            lambda cell: bool(set(str(cell).split(':')) & processed_set))
        is_previous = is_previous & in_processed
    kept = specimens_df.loc[~is_previous]
    return pd.concat([kept, pd.DataFrame(new_rows)], ignore_index=True)


# Day plot functions
# ------------------------------------------------------------------------------------------------------------------
def plot_day_plot_MagIC(specimen_data, 
                   by ='specimen',
                   Mr = 'hyst_mr_mass',
                   Ms = 'hyst_ms_mass',
                   Bcr = 'rem_bcr',
                   Bc = 'hyst_bc',
                   **kwargs):
    """
    Function to plot a Day plot from a MagIC specimens table.

    Parameters
    ----------
    specimen_data : pandas.DataFrame
        DataFrame containing the specimens data.
    by : str
        Column name to group by (default is 'specimen').
    Mr : str
        Column name for the remanence (default is 'hyst_mr_mass').
    Ms : str
        Column name for the saturation magnetization (default is 'hyst_ms_mass').
    Bcr : str
        Column name for the coercivity (default is 'hyst_bcr').
    Bc : str
        Column name for the coercivity of remanence (default is 'hyst_bc').
    **kwargs : keyword arguments
        Additional arguments to pass to the plotting function.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes object containing the plot.
    """
    summary_sats = specimen_data.groupby(by).agg({Mr: 'mean', Ms: 'mean', Bcr: 'mean', Bc: 'mean'}).reset_index()
    summary_sats = summary_sats.dropna()

    fig, ax = plot_day_plot(Mr = summary_sats[Mr],
                       Ms = summary_sats[Ms],
                       Bcr = summary_sats[Bcr],
                       Bc = summary_sats[Bc], 
                       **kwargs)
    return fig, ax
    
def plot_day_plot(Mr, Ms, Bcr, Bc, 
             Mr_Ms_lower=0.05, Mr_Ms_upper=0.5, Bc_Bcr_lower=1.5, Bc_Bcr_upper=4, 
             plot_day_lines = True, 
             plot_MD_slope=True,
             plot_SP_SD_mixing=[10, 15, 25, 30],
             plot_SD_MD_mixing=True,
             color='black', marker='o', 
             label = 'sample', alpha=1, 
             lc='black', lw=0.5, 
             legend=True, figsize=(8,6),
             show_plot=True, return_figure=True):
    '''
    function to plot given Ms, Mr, Bc, Bcr values either as single values or list/array of values 
        plots Mr/Ms vs Bc/Bcr. 

    Parameters
    ----------
    Ms : float or array-like
        saturation magnetization
    Mr : float or array-like
        remanent magnetization
    Bc : float or array-like
        coercivity
    Bcr : float or array-like
        coercivity of remanence
    color : str, optional
        color of the points. The default is 'black'.
    marker : str, optional
        marker style of the points. The default is 'o'.
    label : str, optional
        label for the points. The default is 'sample'.
    alpha : float, optional
        transparency of the points. The default is 1.
    lc : str, optional
        color of the lines. The default is 'black'.
    lw : float, optional
        line width of the lines. The default is 0.5.
    legend : bool, optional
        whether to show the legend. The default is True.
    figsize : tuple, optional
        size of the figure. The default is (6,6).
    show_plot : bool, optional
        whether to show the plot. The default is True.
    return_figure : bool, optional
        whether to return the figure and axes objects. The default is True, so that a different function (plot_day_MagIC) can use it.

    Returns
    -------
    tuple or None
        - If return_figure is True (default), returns (fig, ax).
        - Otherwise, returns None.

    '''
    # force numpy arrays
    Ms = np.asarray(Ms)
    Mr = np.asarray(Mr)
    Bc = np.asarray(Bc)
    Bcr = np.asarray(Bcr)
    Bcr_Bc = Bcr/Bc
    Mr_Ms = Mr/Ms
    fig, ax = plt.subplots(figsize = figsize)
    # plotting SD, PSD, MD regions
    if plot_day_lines:
        ax.axhline(Mr_Ms_lower, color = lc, lw = lw)
        ax.axhline(Mr_Ms_upper, color = lc, lw = lw)
        ax.axvline(Bc_Bcr_lower, color = lc, lw = lw)
        ax.axvline(Bc_Bcr_upper, color = lc, lw = lw)
        ax.text(1.1, 0.55, 'SD', color = 'k', fontsize = 12)
        ax.text(2.0, 0.06, 'PSD', color = 'k', fontsize = 12)
        ax.text(5.0, 0.006, 'MD', color = 'k', fontsize = 12)
    
    if plot_MD_slope:
        MD_Bcr_Bc = np.linspace(4, 20, 100)
        MD_Mr_Ms = 1/MD_Bcr_Bc * 45/480
        ax.plot(MD_Bcr_Bc, MD_Mr_Ms, color = lc, lw = lw, label = 'MD slope')
    if len(plot_SP_SD_mixing) > 0:
        # get the SP saturation curve
        Bcr_Bc_SP, Mr_Ms_SP = SP_saturation_curve()
        ax.plot(Bcr_Bc_SP, Mr_Ms_SP, color = lc, lw = lw, ls='--', label = 'SP saturation curve')
        for i, SP_size in enumerate(plot_SP_SD_mixing):
            mixing_Bcr_Bc, mixing_Mr_Ms = SP_SD_mixture(SP_size)
            # filter out anything above the SP saturation curve
            Mr_Ms_SP_cutoff = np.interp(mixing_Bcr_Bc, Bcr_Bc_SP, Mr_Ms_SP)
            mask = mixing_Mr_Ms < Mr_Ms_SP_cutoff
            mixing_Bcr_Bc = mixing_Bcr_Bc[mask]
            mixing_Mr_Ms = mixing_Mr_Ms[mask]
            ax.plot(mixing_Bcr_Bc, mixing_Mr_Ms, color = 'C'+str(i), lw = lw, ls='--', label = f'SP size {SP_size} nm')
    if plot_SD_MD_mixing:
        # get the SD/MD mixing curve
        mixing_Bcr_Bc, mixing_Mr_Ms = SD_MD_mixture()
        # filter out anything above the SP saturation curve
        Mr_Ms_SP_cutoff = np.interp(mixing_Bcr_Bc, Bcr_Bc_SP, Mr_Ms_SP)
        mask = mixing_Mr_Ms < Mr_Ms_SP_cutoff
        mixing_Bcr_Bc = mixing_Bcr_Bc[mask]
        mixing_Mr_Ms = mixing_Mr_Ms[mask]
        ax.plot(mixing_Bcr_Bc, mixing_Mr_Ms, color = 'k', lw = lw, ls='-.', label = 'SD/MD mixture')
    
    # plot the data
    ax.scatter(Bcr_Bc, Mr_Ms, color = color, marker = marker, label = label, alpha=alpha)
    ax.set_xlim(1, 100)
    ax.set_ylim(0.005, 1)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks([1, 2, 5, 10, 20, 50, 100], [1, 2, 5, 10, 20, 50, 100])
    ax.set_yticks([0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 1], [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 1])
    ax.set_xlabel('B$_{cr}$/B$_{c}$', fontsize=12)
    ax.set_ylabel('M$_{r}$/M$_{s}$', fontsize=12)
    ax.set_title('Day plot', fontsize=14)

    if legend:
        ax.legend(loc='lower right', fontsize=10)
    if show_plot:
        plt.show()
    if return_figure:
        return fig, ax
    return None


def plot_neel_magic(specimen_data, 
                   by ='specimen',
                   Mr = 'hyst_mr_mass',
                   Ms = 'hyst_ms_mass',
                   Bcr = 'rem_bcr',
                   Bc = 'hyst_bc',
                   **kwargs):
    """
    Function to plot a Day plot from a MagIC specimens table.

    Parameters
    ----------
    specimen_data : pandas.DataFrame
        DataFrame containing the specimens data.
    by : str
        Column name to group by (default is 'specimen').
    Mr : str
        Column name for the remanence (default is 'hyst_mr_mass').
    Ms : str
        Column name for the saturation magnetization (default is 'hyst_ms_mass').
    Bcr : str
        Column name for the coercivity (default is 'hyst_bcr').
    Bc : str
        Column name for the coercivity of remanence (default is 'hyst_bc').
    **kwargs : keyword arguments
        Additional arguments to pass to the plotting function.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes object containing the plot.
    """
    summary_stats = specimen_data.groupby(by).agg({Mr: 'mean', Ms: 'mean', Bcr: 'mean', Bc: 'mean'}).reset_index()
    summary_stats = summary_stats.dropna()

    ax = plot_neel(Mr = summary_stats[Mr],
                Ms = summary_stats[Ms],
                Bc = summary_stats[Bc], 
                **kwargs)
    return ax


def plot_neel(Mr, Ms, Bc, color='black', marker = 'o', label = 'sample', alpha=1, lc = 'black', lw=0.5, legend=True, axis_scale='linear', figsize = (5, 5)):
    """
    Generate a Néel plot (squareness-coercivity) of Mr/Ms versus Bc from hysteresis data.

    This plot shows the ratio of remanent to saturation magnetization
    (Mr/Ms) plotted against the coercivity (Bc). It is useful for 
    characterizing magnetic domain states in rock magnetic samples.

    Parameters
    ----------
    Mr : array-like
        Saturation remanence values of the samples.
    Ms : array-like
        Saturation magnetization values of the samples.
    Bc : array-like
        Coercivity values of the samples.
    color : str, optional
        Color of the scatter points. Default is "black".
    marker : str, optional
        Marker style for scatter points. Default is "o".
    label : str, optional
        Label for the sample to be displayed in the legend. Default is "sample".
    alpha : float, optional
        Transparency of the scatter points. Default is 1 (opaque).
    lc : str, optional
        Color of the grid lines. Default is "black".
    lw : float, optional
        Line width of the grid lines. Default is 0.5.
    legend : bool, optional
        Whether to show the legend. Default is True.
    axis_scale : str, optional
        Scale for both axes: "linear" or "log". Default is "linear".
    figsize : tuple of int, optional
        Figure size in inches (width, height). Default is (5, 5).

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib axes object containing the plot.
    """
    assert axis_scale in ['linear', 'log'], "axis_scale must be 'linear' or 'log'"
    # force numpy arrays
    Ms = np.asarray(Ms)
    Mr = np.asarray(Mr)
    Bc = np.asarray(Bc)
    Mr_Ms = Mr/Ms
    _, ax = plt.subplots(figsize = figsize)
    ax.scatter(Bc, Mr_Ms, color = color, marker = marker, label = label, alpha=alpha, zorder = 100)
    ax.set_xlabel('B$_c$ (T)', fontsize=12)
    ax.set_ylabel('M$_r$/M$_s$', fontsize=12)
    if axis_scale == 'linear':
        ax.set_xscale('linear')   
        ax.set_yscale('linear')
    else:
        ax.set_xscale('log')   
        ax.set_yscale('log')
    if legend:
        ax.legend(loc='upper left', fontsize=12)

    ax.grid(True, which='both', linestyle='--', linewidth=lw, color=lc)
    return ax


def Langevin_alpha(V, Ms, H, T):
    '''
    Langevin alpha calculation

    Parameters
    ----------
    V : float
        volume of the particle
    Ms : float
        saturation magnetization
    H : float
        applied field
    T : float
        temperature in Kelvin

    Returns
    -------
    alpha : float
        Langevin alpha value
    '''
    mu0 = 4 * np.pi * 1e-7
    k = 1.38064852e-23

    return mu0*Ms * V * H / (k * T)


def Langevin(alpha):
    '''
    Langevin function

    Parameters
    ----------
    alpha : float
        Langevin alpha value

    Returns
    -------
    L : float
        Langevin function value
    '''
    return 1 / np.tanh(alpha) - 1 / alpha


def magnetite_Ms(T):
    '''
    Magnetite saturation magnetization calculation

    Parameters
    ----------
    T : float
        temperature in Celsius

    Returns
    -------
    Ms : float
        saturation magnetization value
    '''
    return 737.384 * 51.876 * (580 - T)**0.4


def chi_SP(SP_size, T):
    '''
    SP size distribution function

    Parameters
    ----------
    SP_size : float
        size of the superparamagnetic particle in nm
    T : float
        temperature in Kelvin

    Returns
    -------
    chi : float
        susceptibility value
    '''
    mu0 = 4 * np.pi * 1e-7
    k = 1.38064852e-23
    Ms = magnetite_Ms(T - 273.15)
    V = 4/3*np.pi*(SP_size/2)**3 / 1e27
    return mu0 * V * Ms**2 / 3 / k / T


def SP_SD_mixture(SP_size, SD_Mr_Ms = 0.5, SD_Bcr_Bc = 1.25, X_sd = 3, T = 300):
    '''
    function to calculate the SP/SD mixture curve according to Dunlop (2002)
    Parameters
    ----------
    SP_size : float
        size of the superparamagnetic particle in nm
    SD_Mr_Ms : float, optional
        remanent to saturation magnetization ratio. The default is 0.5.
    SD_Bcr_Bc : float, optional
        remanent coercivity to coercivity ratio. The default is 1.25.
    X_sd : float, optional
        approximate Mrs/Bc slope. The default is 3 for magnetite
    T : float, optional
        temperature in Kelvin. The default is 300.
    Returns
    -------
    Bcr_Bc : numpy.ndarray
        coercivity ratio array
    Mrs_Ms : numpy.ndarray
        saturation magnetization ratio array
    '''
    f_sd = 1/np.logspace(0, 2, 100)
    f_sp = 1 - f_sd
    Mrs_Ms = f_sd * SD_Mr_Ms
    X_sp = chi_SP(SP_size, T)
    Bcr_Bc = 1 / (f_sd * X_sd / (f_sd * X_sd + f_sp * X_sp)) * SD_Bcr_Bc

    return Bcr_Bc, Mrs_Ms


def SP_saturation_curve(SD_Mr_Ms=0.5, SD_Bcr_Bc = 1.25):
    '''
    function to calculate the SP saturation curve according to Dunlop (2002)

    Parameters
    ----------
    SD_Mr_Ms : float, optional
        saturation magnetization ratio. The default is 0.5.
    SD_Bcr_Bc : float, optional
        remanence coercivity to coercivity ratio. The default is 1.25.
    Returns
    -------
    Bcr_Bc : numpy.ndarray
        coercivity ratio array
    Mrs_Ms : numpy.ndarray
        saturation magnetization ratio array
    '''
    f_sp = np.linspace(0, 1/3, 100)
    f_sd = 1 - f_sp
    Mrs_Ms = f_sd * SD_Mr_Ms
    Bcr_Bc = 1 / (1 - (f_sp/f_sd) / SD_Mr_Ms) * SD_Bcr_Bc
    return Bcr_Bc, Mrs_Ms


def SD_MD_mixture(Mr_Ms_SD = 0.5, Mr_Ms_MD = 0.019,
                  Bc_SD = 400, Bc_MD = 43,
                  Bcr_SD = 500, Bcr_MD = 230,
                  X_sd = 0.6, X_MD = 0.209,
                  Xr_SD = 0.48, Xr_MD = 0.039):
    '''
    function to calculate the SD/MD mixture curve according to Dunlop (2002)
    Parameters
    ----------
    Mr_Ms_SD : float
        remanent to saturation magnetization ratio for SD. The default is 0.5.
    Mr_Ms_MD : float
        remanent to saturation magnetization ratio for MD. The default is 0.019.
    Bc_SD : float
        coercivity for SD. The default is 400.
    Bc_MD : float
        coercivity for MD. The default is 43.
    Bcr_SD : float
        coercivity of remanence for SD. The default is 500.
    Bcr_MD : float
        coercivity of remanence for MD. The default is 230.
    X_sd : float
        approximate Mrs/Bc slope for SD. The default is 0.6.
    X_MD : float
        approximate Mrs/Bc slope for MD. The default is 0.209.
    Xr_SD : float
        approximate Mrs/Bcr slope for SD. The default is 0.48.
    Xr_MD : float
        approximate Mrs/Bcr slope for MD. The default is 0.039.
    Returns
    -------
    Bcr_Bc : numpy.ndarray
        coercivity ratio array
    Mrs_Ms : numpy.ndarray
        saturation magnetization ratio array

    * the default values are fro the IRM database
    '''
    f_sd = np.linspace(0, 1, 100)
    f_md = 1 - f_sd
    Mrs_Ms = f_sd * Mr_Ms_SD + f_md * Mr_Ms_MD
    Bc = (f_sd * X_sd * Bc_SD + f_md * X_MD * Bc_MD) / (f_sd * X_sd + f_md * X_MD)
    Bcr = (f_sd * Xr_SD * Bcr_SD + f_md * Xr_MD * Bcr_MD) / (f_sd * Xr_SD + f_md * Xr_MD)
    Bcr_Bc = Bcr / Bc
    return Bcr_Bc, Mrs_Ms

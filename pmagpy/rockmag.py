import pandas as pd
import numpy as np
import copy

from scipy.optimize import minimize, brent, least_squares, minimize_scalar
from scipy.signal import savgol_filter
from scipy.interpolate import UnivariateSpline

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patches as patches

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
    from bokeh.models import HoverTool, Label
    from bokeh.embed import components
    from bokeh.palettes import Category10
    from bokeh.models import ColumnDataSource
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


def make_experiment_df(measurements):
    """
    Creates a DataFrame of unique experiments from the measurements DataFrame.

    Args:
        measurements (pd.DataFrame): The DataFrame containing measurement data with columns 
            'specimen', 'method_codes', and 'experiment'.

    Returns:
        pd.DataFrame: A DataFrame containing unique combinations of 'specimen', 'method_codes', 
            and 'experiment'.
    """
    experiments = measurements.groupby(['specimen', 'method_codes', 'experiment']).size().reset_index().iloc[:, :3]
    return experiments


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


def ms_t_plot(
    data,
    temperature_column="meas_temp",
    magnetization_column="magn_mass",
    temp_unit="K",
    interactive=False,
    return_figure=False,
    show_plot=True,
):
    """
    Plot magnetization vs. temperature, either static or interactive,
    with option to display in K or °C.

    Parameters
    ----------
    data : pandas.DataFrame or array-like
        Table or array containing temperature and magnetization.
    temperature_column : str
        Name of the temperature column in `data` (assumed in K).
    magnetization_column : str
        Name of the magnetization column in `data`.
    temp_unit : {'K','C'}, default 'K'
        Units for the x-axis: 'K' for Kelvin or 'C' for Celsius.
    interactive : bool, default False
        If True, use Bokeh for an interactive plot.
    return_figure : bool, default False
        If True, return the figure object(s).
    show_plot : bool, default True
        If True, display the plot.

    Returns
    -------
    (fig, ax) or bokeh layout or None
        Matplotlib Figure and Axes or Bokeh layout if `return_figure` is True;
        otherwise None.
    """
    # extract data arrays
    T = np.asarray(data[temperature_column], dtype=float)
    M = np.asarray(data[magnetization_column], dtype=float)

    # convert to Celsius if requested
    if temp_unit == "C":
        T = T - 273.15
        x_label = "Temperature (°C)"
    else:
        x_label = "Temperature (K)"

    if interactive:
        tools = [HoverTool(tooltips=[("T", "@x"), ("M", "@y")]),
                 "pan,box_zoom,wheel_zoom,reset,save"]
        p = figure(
            title="M vs T",
            x_axis_label=x_label,
            y_axis_label="Magnetization",
            tools=tools,
            sizing_mode="stretch_width"
        )
        p.xaxis.axis_label_text_font_style = "normal"
        p.yaxis.axis_label_text_font_style = "normal"
        p.line(T, M, legend_label="M(T)", line_width=2)
        p.scatter(T, M, size=6, alpha=0.6, legend_label="M(T)")
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"

        layout = gridplot([[p]], sizing_mode="stretch_width")
        if show_plot:
            show(layout)
        if return_figure:
            return layout
        return None

    fig, ax = plt.subplots()
    ax.plot(T, M, "o-", label="M(T)")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Magnetization")
    ax.set_title("M vs T")
    ax.legend()
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
        tools = [HoverTool(tooltips=[("T","@x"),("M","@y")]), "pan,box_zoom,reset,save"]  
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
        if show_plot: show(layout)  
        return layout if return_figure else None  

    # Matplotlib branch  
    rows = 1 + (1 if plot_derivative else 0)  
    cols = 2  
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))  
    axes = axes.reshape(rows, cols)  

    if not fc_zfc_present:  
        axes[0,0].set_visible(False)  
        if plot_derivative: axes[1,0].set_visible(False)  
    if not rtsirm_present:  
        axes[0,1].set_visible(False)  
        if plot_derivative: axes[1,1].set_visible(False)  

    if fc_zfc_present:  
        ax = axes[0,0]  
        if fc is not None: ax.plot(fc["meas_temp"], fc["magn_mass"], color=fc_color, marker=fc_marker, label="FC")  
        if zfc is not None: ax.plot(zfc["meas_temp"], zfc["magn_mass"], color=zfc_color, marker=zfc_marker, label="ZFC")  
        ax.set_title("LTSIRM Data"); ax.set_xlabel("Temperature (K)"); ax.set_ylabel("Magnetization"); ax.legend(); ax.grid(True)  

    if rtsirm_present:  
        ax = axes[0,1]  
        if rc is not None: ax.plot(rc["meas_temp"], rc["magn_mass"], color=rtsirm_cool_color, marker=rtsirm_cool_marker, label="cool")  
        if rw is not None: ax.plot(rw["meas_temp"], rw["magn_mass"], color=rtsirm_warm_color, marker=rtsirm_warm_marker, label="warm")  
        ax.set_title("RTSIRM Data"); ax.set_xlabel("Temperature (K)"); ax.set_ylabel("Magnetization"); ax.legend(); ax.grid(True)  

    if plot_derivative and fc_zfc_present:  
        ax = axes[1,0]  
        if fcd is not None: ax.plot(fcd["T"], fcd["dM_dT"], color=fc_color, marker=fc_marker, label="FC dM/dT")  
        if zfcd is not None: ax.plot(zfcd["T"], zfcd["dM_dT"], color=zfc_color, marker=zfc_marker, label="ZFC dM/dT")  
        ax.set_title("LTSIRM Derivative"); ax.set_xlabel("Temperature (K)"); ax.set_ylabel("dM/dT"); ax.legend(); ax.grid(True)  

    if plot_derivative and rtsirm_present:  
        ax = axes[1,1]  
        if rcd is not None: ax.plot(rcd["T"], rcd["dM_dT"], color=rtsirm_cool_color, marker=rtsirm_cool_marker, label="cool dM/dT")  
        if rwd is not None: ax.plot(rwd["T"], rwd["dM_dT"], color=rtsirm_warm_color, marker=rtsirm_warm_marker, label="warm dM/dT")  
        ax.set_title("RTSIRM Derivative"); ax.set_xlabel("Temperature (K)"); ax.set_ylabel("dM/dT"); ax.legend(); ax.grid(True)  

    fig.tight_layout()  
    if show_plot: plt.show()  
    return fig if return_figure else None  


def make_mpms_plots_dc(measurements):
    """Create a UI to select specimen and plot MPMS data in Matplotlib or Bokeh.

    Parameters:
        measurements (pandas.DataFrame): DataFrame with 'specimen' and
            'method_codes'.
    """
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
    
    remanence_loss = np.trapz(mgt_dM_dT, temps_dM_dT_background)

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
    #plt.show()

    return verwey_estimate, remanence_loss


def interactive_verwey_estimate(measurements, specimen_dropdown, method_dropdown):
    
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

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(12, 6))
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
    
    
def interactive_goethite_removal(measurements, specimen_dropdown):
    
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
        show_plot=True):
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

    Returns
    -------
    fig, ax or (fig, axes) or Bokeh layout or None
    """
    if phase not in ['in', 'out', 'both']:
        raise ValueError('phase must be "in", "out", or "both"')
    freqs = ([frequency] if frequency is not None
             else experiment['meas_freq'].unique().tolist())
    if frequency is not None and frequency not in freqs:
        raise ValueError(f'frequency must be one of {freqs}')

    if interactive:
        tools = [
            HoverTool(tooltips=[('T', '@x'), ('χ', '@y')]),
            'pan,box_zoom,wheel_zoom,reset,save']
        n = len(freqs)
        palette = Category10[n] if n <= 10 else Category10[10]
        figs = []

        if phase in ['in', 'out']:
            p = figure(
                title=f'AC χ ({phase} phase)',
                x_axis_label='Temperature (K)',
                y_axis_label='χ (m³/kg)',
                tools=tools,
                width=int(figsize[0] * 100),
                height=int(figsize[1] * 100))
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
            p.legend.location = 'top_left'
            p.legend.click_policy = "hide"
            figs = [p]
        else:
            p1 = figure(
                title='AC χ in phase',
                x_axis_label='Temperature (K)',
                y_axis_label='χ (m³/kg)',
                tools=tools,
                width=int(figsize[0] * 50),
                height=int(figsize[1] * 100))
            p2 = figure(
                title='AC χ out phase',
                x_axis_label='Temperature (K)',
                y_axis_label='χ (m³/kg)',
                tools=tools,
                width=int(figsize[0] * 50),
                height=int(figsize[1] * 100))
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
            p1.legend.location = p2.legend.location = 'top_left'
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
        ax.legend()
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
    ax1.legend()
    ax2.set_xlabel('Temperature (K)')
    ax2.set_ylabel('χ (m³/kg)')
    ax2.set_title('AC χ out phase')
    ax2.legend()
    if show_plot:
        plt.show()
    if return_figure:
        return fig, (ax1, ax2)


# hysteresis functions
# ------------------------------------------------------------------------------------------------------------------

def extract_hysteresis_data(df, specimen_name):
    """
    Extracts and separates Hysteresis data 
    for a specific specimen from a dataframe.

    This function filters data for a given specimen and separates it based on 
    different MagIC measurement method codes. It specifically looks for data 
    corresponding to 'LP-HYS' Hysteresis Data

    Parameters:
        df (pandas.DataFrame): The dataframe containing MPMS measurement data.
        specimen_name (str): The name of the specimen to filter data for.

    Returns:
        tuple: A tuple containing four pandas.DataFrames:
            - fc_data: Data filtered for 'LP-FC' method if available, otherwise an empty DataFrame.
            - zfc_data: Data filtered for 'LP-ZFC' method if available, otherwise an empty DataFrame.
            - rtsirm_cool_data: Data filtered for 'LP-CW-SIRM:LP-MC' method if available, otherwise an empty DataFrame.
            - rtsirm_warm_data: Data filtered for 'LP-CW-SIRM:LP-MW' method if available, otherwise an empty DataFrame.

    Example:
        >>> fc, zfc, rtsirm_cool, rtsirm_warm = extract_mpms_data_dc(measurements_df, 'Specimen_1')
    """

    specimen_df = df[df['specimen'] == specimen_name]

    hyst_data = specimen_df[specimen_df['method_codes'].str.contains('LP-HYS', na=False)]

    return hyst_data

def plot_hysteresis_loop(field, magnetization, specimen_name, p=None, line_color='grey', line_width=1, label='', legend_location='bottom_right'):
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
    if not _HAS_BOKEH:
        print("Bokeh is not installed. Please install it to enable hysteresis data processing.")
        return
    
    assert len(field) == len(magnetization), 'Field and magnetization arrays must be the same length'
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

    return p

def split_hysteresis_loop(field, magnetization):
    '''
    function to split a hysteresis loop into upper and lower branches
        by the change of sign in the applied field gradient

    Parameters
    ----------
    field : numpy array or list
        hysteresis loop field values
    magnetization : numpy array or list
        hysteresis loop magnetization values

    Returns
    -------
    upper_branch : tuple
        tuple of field and magnetization values for the upper branch
    lower_branch : tuple
        tuple of field and magnetization values for the lower branch
    '''
    assert len(field) == len(magnetization), 'Field and magnetization arrays must be the same length'

    # identify loop turning point by change in sign of the field difference
    # split the data into upper and lower branches
    field_gradient = np.gradient(field)
    # There should just be one turning point in the field gradient
    turning_points = np.where(np.diff(np.sign(field_gradient)))[0]
    if len(turning_points) > 1:
        raise ValueError('More than one turning point found in the gradient of the applied field')
    turning_point = turning_points[0]
    upper_branch = [field[:turning_point+1], magnetization[:turning_point+1]]
    # sort the upper branch in reverse order
    upper_branch = [field[:turning_point+1][::-1], magnetization[:turning_point+1][::-1]]
    lower_branch = [field[turning_point+1:], magnetization[turning_point+1:]]
    
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

    upper_branch, lower_branch = split_hysteresis_loop(field, magnetization)

    # calculate the average field step size
    field_step = np.mean(np.abs(np.diff(upper_branch[0])))
    # grid the hysteresis loop
    upper_field = np.arange(np.max(field), 0, -field_step)
    upper_field = np.concatenate([upper_field, -upper_field[::-1]])
    lower_field = upper_field[::-1]
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
    Linear regression fit: y = intercept + slope * x
    Returns: intercept, slope, R^2
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
    ss_res = np.sum((y_pred - np.mean(yarr))**2)

    # R^2 score
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1

    return intercept, slope, r2

def loop_H_off(loop_fields, loop_moments, H_shift):
    """
    Estimates a vertical shift (V_shift) and returns R² of a reflected loop.
    
    Arguments:
    - loop_fields: List or array of magnetic field values.
    - loop_moments: Corresponding list or array of magnetic moments.
    - H_shift: Horizontal shift to apply to loop_fields.
    
    Returns:
    - r2: R-squared value from linear regression between original and reflected data.
    - V_shift: Estimated vertical shift (mean of linear fit x-intercept).
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
        return 0.0, 0.0  # Not enough points for regression

    intercept, slope, r2 = linefit(x1, y1)
    M_shift = intercept / 2

    result = {'slope': slope, 'M_shift': M_shift, 'r2': r2}
    return result

def loop_Hshift_brent(loop_fields, loop_moments):
    def objective(H_shift):
        result = loop_H_off(loop_fields, loop_moments, H_shift)
        return result['r2']
    
    ax = -np.max(loop_fields)/2
    bx = 0
    cx = -ax
    result = minimize_scalar(objective, method='brent', bracket=(ax, bx, cx), tol=1e-6)

    opt_H_off = result.x
    opt_shift = loop_H_off(loop_fields, loop_moments, opt_H_off)
    opt_r2 = opt_shift['r2']
    opt_M_off = opt_shift['M_shift']

    return opt_r2, opt_H_off, opt_M_off

def calc_Q(H, M, type='Q'):
    '''
    function for calculating quality factor Q for a hysteresis loop
        Q factor is defined by the log10 of the signal to noise ratio
        where signal is the sum of the square of the data 
        which is the averaged sum over the upper and lower branches for Q
        and is the sum of the square of the upper branch for Qf
    '''
    assert type in ['Q', 'Qf'], 'type must be either Q or Qf'
    H = np.array(H)
    M = np.array(M)
    upper_branch, lower_branch = split_hysteresis_loop(H, M)  
    Me = upper_branch[1] + lower_branch[1][::-1]
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

    M_sn, Q = calc_Q(grid_field, grid_magnetization)

    # re-gridding after offset correction to ensure symmetry
    centered_H, centered_M = grid_hysteresis_loop(grid_field-H_offset/2, grid_magnetization-M_offset)

    results = {'centered_H':centered_H, 
               'centered_M': centered_M, 
               'opt_H_offset':float(H_offset/2), 
               'opt_M_offset':float(M_offset), 
               'R_squared':float(R_squared), 
               'M_sn':float(M_sn), 
               'Q':float(Q),
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
    slope : float
        slope of the linear fit
        can be interpreted to be the paramagnetic/diamagnetic susceptibility
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

    # invert points in the third quadrant to the first
    high_field = np.abs(field[high_field_index])
    high_field_magnetization = np.abs(magnetization[high_field_index])

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
    Finds the x-value where y crosses a given y_target, nearest to x = 0.
    Uses linear interpolation between adjacent points that bracket y_target.

    Parameters:
        x (array-like): x-values
        y (array-like): y-values
        y_target (float): y-value at which to find crossing (default: 0)

    Returns:
        x_cross (float or None): interpolated x at y = y_target nearest to x = 0, or None if not found
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
    Mrh : float
        remanent magnetization value
    Mih : float
        induced magnetization value
    Me : numpy array
        error on M(H), calculated as the subtraction of the inverted lower branch from the upper branch
    Brh : float
        median field of Mrh

    '''
    # calculate Mrh bu subtracting the upper and lower branches of a hysterisis loop
    grid_field = np.array(grid_field)
    grid_magnetization = np.array(grid_magnetization)

    grid_field = grid_field
    grid_magnetization = grid_magnetization

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
    Me = upper_branch[1] + lower_branch[1][::-1]
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

    SSPE = np.sum((upper_branch[1] - (-lower_branch[1][::-1])) ** 2)  / 2
    SSLF = SSD - SSPE
    MSR = SSR 
    MSD = SSD / (len(high_field) - 2)
    MSPE = SSPE / (len(high_field) / 2)
    MSLF = SSLF / (len(high_field)/2 - 2)

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
    '''
    function for testing the saturation of a hysteresis loop
        which is based on the testing of linearity of the loop in field ranges of 60%, 70%, and 80% of the maximum field (<97%)
    '''
    
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


def loop_closure_test(H, Mrh, HF_cutoff=0.8):
    '''
    function for testing if the loop is open
    
    Parameters
    ----------
    H: array-like
        field values
    Mrh: array-like
        remanence componentt
    HF_cutoff: float
        high field cutoff value taken as percentage of the max field value

    Returns
    -------
    SNR: float
        high field signal to noise ratio
    HAR: float
        high field area ratio
    '''
    assert len(H) == len(Mrh), 'H, Mrh must have the same length'
    pos_H_index = np.where(H > 0)
    neg_H_index = np.where(H < 0)
    pos_H = H[pos_H_index]
    neg_H = H[neg_H_index]
    pos_Mrh = Mrh[pos_H_index]
    neg_Mrh = Mrh[neg_H_index]

    pos_HF_index = np.where(H > HF_cutoff*np.max(H))
    neg_HF_index = np.where(H < -HF_cutoff*np.max(H))
    pos_HF = H[pos_HF_index]
    neg_HF = H[neg_HF_index]
    pos_HF_Mrh = Mrh[pos_HF_index]
    neg_HF_Mrh = Mrh[neg_HF_index]
    
    average_Mrh = (pos_Mrh - neg_Mrh[::-1])/2
    # replace all negative values with 0
    average_Mrh[average_Mrh < 0] = 0
    average_HF_Mrh = (pos_HF_Mrh - neg_HF_Mrh[::-1])/2
    # replace all negative values with 0
    average_HF_Mrh[average_HF_Mrh < 0] = 0
    HF_Mrh_noise = pos_HF_Mrh + neg_HF_Mrh[::-1]
    # replace all negative values with 0
    HF_Mrh_noise[HF_Mrh_noise < 0] = 0

    HF_Mrh_signal_RMS = np.sqrt(np.mean(average_HF_Mrh**2))
    HF_Mrh_noise_RMS = np.sqrt(np.mean(HF_Mrh_noise**2))
    SNR = 20*np.log10(HF_Mrh_signal_RMS/HF_Mrh_noise_RMS)

    total_Mrh_area = np.trapz(pos_Mrh, pos_H) + np.trapz(-neg_Mrh[::-1], -neg_H[::-1])
    total_HF_Mrh_area = np.trapz(average_Mrh, pos_H)

    HAR = 20*np.log10(total_HF_Mrh_area/total_Mrh_area)
    loop_is_closed = (SNR < 8) or (HAR < -48)

    results = {'SNR':float(SNR), 
               'HAR':float(HAR), 
               'loop_is_closed':bool(loop_is_closed),
               }
    return results


def drift_correction_Me(H, M):
    '''
    default IRM drift correction algorithm based on Me 

    Parameters
    ----------
    H : numpy array
        field values
    M : numpy array
        magnetization values
    '''
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
    corrected_magnetization = [M_ce * ((i-1)/(len(field)-1) - 1/2) + magnetization[i] for i in range(len(field))]

    return np.array(corrected_magnetization)

def symmetric_averaging_drift_corr(field, magnetization):
    
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
    '''
    function for calculating the IRM non-linear fit

    Parameters
    ----------
    H : numpy array
        field values
    chi_HF : float
        high field susceptibility, converted to Tesla to match the unit of the field
    Ms : float
        saturation magnetization
    a_1 : float
        coefficient for H^(-1), needs to be negative
    a_2 : float
        coefficient for H^(-2), needs to be negative

    '''
    chi_HF = chi_HF/(4*np.pi/1e7)
    return chi_HF * H + Ms + a_1 * H**(-1) + a_2 * H**(-2)

def IRM_nonlinear_fit_cost_function(params, H, M_obs):
    '''
    cost function for the IRM non-linear least squares fit optimization

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
        - 'Fnl_lin': float, ratio comparing nonlinear vs. linear fit  
    '''
    HF_index = np.where((np.abs(H) >= HF_cutoff*np.max(np.abs(H))) & (np.abs(H) <= 0.97*np.max(np.abs(H))))[0]

    HF_field = np.abs(H[HF_index])
    HF_magnetization = np.abs(M[HF_index])

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

    # let's also report the Fnl_lin which is a measure of whether the nonlinear fit is better than a linear fit
    # let's first make a linear fit
    linear_fit_ANOVA = ANOVA(HF_field, HF_magnetization)
    R_squared_l = 1 - linear_fit_ANOVA['R_squared']

    # now calculate the nonlinear fit SST
    nl_SST = np.sum((HF_magnetization - np.mean(HF_magnetization)) ** 2)

    # sum of squares due to regression
    nl_SSR = np.sum((nonlinear_fit - np.mean(HF_magnetization)) ** 2)
    
    # the remaining unexplained variation (noise and lack of fit)
    nl_SSD = np.sum((HF_magnetization - nonlinear_fit) ** 2)
    
    R_squared_nl = 1 - nl_SSR/nl_SST 

    # calculate the Fnl_lin stat
    Fnl_lin = R_squared_l / R_squared_nl

    final_result['Fnl_lin'] = Fnl_lin
    final_result_dict = dict_in_native_python(final_result)
    return final_result_dict


def process_hyst_loop(field, magnetization, specimen_name, show_results_table=True):
    '''
    function to process a hysteresis loop following the IRM decision tree
    Parameters
    ----------
    field : array
        array of field values
    magnetization : array
        array of magnetization values
        
    Returns
    -------
    results : dict
        dictionary with the hysteresis processing results and a Bokeh plot
    '''
    # first grid the data into symmetric field values
    grid_fields, grid_magnetizations = grid_hysteresis_loop(field, magnetization)

    # test linearity of the gridded original loop
    loop_linearity_test_results = hyst_linearity_test(grid_fields, grid_magnetizations)

    # loop centering
    loop_centering_results = hyst_loop_centering(grid_fields, grid_magnetizations)
    # check if the quality factor Q is < 2
    if loop_centering_results['Q'] < 2:
        # in case the loop quality is bad, no field correction is applied
        loop_centering_results['opt_H_offset'] = 0
        loop_centering_results['centered_H'] = grid_fields

    centered_H, centered_M = loop_centering_results['centered_H'], loop_centering_results['centered_M']

    # drift correction
    drift_corr_M = drift_correction_Me(centered_H, centered_M)

    # calculate Mr, Mrh, Mih, Me, Brh
    H, Mr, Mrh, Mih, Me, Brh = calc_Mr_Mrh_Mih_Brh(centered_H, drift_corr_M)

    # check if the loop is closed
    loop_closure_test_results = loop_closure_test(H, Mrh)

    # check if the loop is saturated (high field linearity test)
    loop_saturation_stats = hyst_loop_saturation_test(centered_H, drift_corr_M)

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
    E_hyst = np.trapz(Mrh, H)
    sigma = np.log(E_hyst / 2 / Bc / Ms)

    # plot original loop
    p = plot_hysteresis_loop(grid_fields, grid_magnetizations, specimen_name, line_color='orange', label='raw loop')
    # plot centered loop
    p_centered = plot_hysteresis_loop(centered_H, centered_M, specimen_name, p=p, line_color='red', label=specimen_name+' offset corrected')
    # plot drift corrected loop
    p_drift_corr = plot_hysteresis_loop(centered_H, drift_corr_M, specimen_name, p=p_centered, line_color='pink', label=specimen_name+' drift corrected')
    # plot slope corrected loop
    p_slope_corr = plot_hysteresis_loop(centered_H, slope_corr_M, specimen_name, p=p_drift_corr, line_color='blue', label=specimen_name+' slope corrected')
    # plot Mrh
    p_slope_corr.line(H, Mrh, line_color='green', legend_label='Mrh', line_width=1)
    p_slope_corr.line(H, Mih, line_color='purple', legend_label='Mih', line_width=1)
    p_slope_corr.line(H, Me, line_color='brown', legend_label='Me', line_width=1)
    show(p)
    results = {'gridded_H': grid_fields, 
               'gridded_M': grid_magnetizations, 
               'linearity_test_results': loop_linearity_test_results,
               'loop_is_linear': loop_linearity_test_results['loop_is_linear'],
               'FNL': loop_linearity_test_results['FNL'],
               'loop_centering_results': loop_centering_results,
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
    
    if show_results_table:
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

    Returns
    -------
    list of dict
        Each dict is the output of `process_hyst_loop` for one specimen.
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
        )
        results.append(res)
    return results


def add_hyst_stats_to_specimens_table(specimens_df, experiment_name, hyst_results):
    '''
    function to export the hysteresis data to a MagIC specimen data table
    
    Parameters
    ----------
    specimens_df : pandas.DataFrame
        dataframe with the specimens data
    experiment_name : str
        name of the experiment
    hyst_results : dict
        dictionary with the hysteresis data
        as output from the rmag.process_hyst_loop function

    updates the specimen table in place
    '''

    result_keys_MagIC = ['specimen',  
                        'Ms', 
                        'Mr', 
                        'Bc',  
                        'chi_HF']

    MagIC_columns=['specimen',  
                    'hyst_ms_mass', 
                    'hyst_mr_mass', 
                    'hyst_bc',  
                    'hyst_xhf']

    # add MagIC available columns to the specimens table
    for result_key, col in zip(result_keys_MagIC, MagIC_columns):
        if col not in specimens_df.columns:
            # add the column to the specimens table
            specimens_df[col] = np.nan
    
            specimens_df.loc[specimens_df['experiments'] == experiment_name, col] = hyst_results[result_key]
    
    # dump the rest of the stats to the description column
    additional_keys = ['Q', 'Qf', 'sigma',
                'Brh', 'FNL', 'FNL60', 'FNL70', 'FNL80', 
                'Fnl_lin', 'loop_is_linear', 'loop_is_closed', 'loop_is_saturated']
    additional_stats_dict = {}
    for key in additional_keys:
        additional_stats_dict[key] = hyst_results[key]
        
    # check if the description cell is type string
    if isinstance(specimens_df[specimens_df['experiments'] == experiment_name]['description'].iloc[0], str):
        # unpack the string to a dict, then add the new stats, then pack it back to a string
        description_dict = eval(specimens_df[specimens_df['experiments'] == experiment_name]['description'].iloc[0])
        for key in additional_keys:
            if key in description_dict:
                # if the key already exists, update it
                description_dict[key] = hyst_results[key]
            else:
                # if the key does not exist, add it
                description_dict[key] = hyst_results[key]
        # pack the dict back to a string
        specimens_df.loc[specimens_df['experiments'] == experiment_name, 'description'] = str(description_dict)
    else:
        # if not, create a new dict
        specimens_df.loc[specimens_df['experiments'] == experiment_name, 'description'] = str(additional_stats_dict)
    return 

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
    return_figure=False,
):
    """
    Plot the high-temperature X–T curve, and optionally its derivative
    and reciprocal using Bokeh.

    Parameters:
        experiment (pandas.DataFrame):
            The IRM experiment data exported into MagIC format.
        temperature_column (str, optional):
            Name of the temperature column. Defaults to "meas_temp".
        magnetic_column (str, optional):
            Name of the susceptibility column. Defaults to "susc_chi_mass".
        temp_unit (str, optional):
            Unit of temperature, either "K" or "C". Defaults to "C".
        smooth_window (int, optional):
            Window size for running-average smoothing. Defaults to 0.
        remove_holder (bool, optional):
            If True, subtract the minimum holder signal. Defaults to True.
        plot_derivative (bool, optional):
            If True, generate dX/dT plot. Defaults to True.
        plot_inverse (bool, optional):
            If True, generate 1/X plot. Defaults to False.
        return_figure (bool, optional):
            If True, return the Bokeh figure objects. Defaults to False.

    Returns:
        tuple[bokeh.plotting.figure.Figure, ...] or None:
            The requested Bokeh figures if return_figure is True;
            otherwise, None.
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
        raise ValueError('temp_unit must be either "K" or "C"')

    if remove_holder:
        holder_w = min(warm_X)
        holder_c = min(cool_X)
        warm_X = [X - holder_w for X in warm_X]
        cool_X = [X - holder_c for X in cool_X]

    swT, swX = smooth_moving_avg(warm_T, warm_X, smooth_window)
    scT, scX = smooth_moving_avg(cool_T, cool_X, smooth_window)

    width = 900
    height = int(width / 1.618)
    title = experiment["specimen"].unique()[0]

    p = figure(
        title=title,
        width=width,
        height=height,
        x_axis_label=f"Temperature (°{temp_unit})",
        y_axis_label="k (m³ kg⁻¹)",
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )

    r_warm_c = p.scatter(
        warm_T, warm_X, legend_label="Heating",
        color="red", alpha=0.5, size=6,
    )
    r_warm_l = p.line(
        swT, swX, legend_label="Heating – smoothed",
        line_width=2, color="red",
    )

    r_cool_c = p.scatter(
        cool_T, cool_X, legend_label="Cooling",
        color="blue", alpha=0.5, size=6,
    )
    r_cool_l = p.line(
        scT, scX, legend_label="Cooling – smoothed",
        line_width=2, color="blue",
    )

    p.add_tools(
        HoverTool(renderers=[r_warm_c, r_warm_l],
                  tooltips=[("T", "@x"), ("Heating X", "@y")])
    )
    p.add_tools(
        HoverTool(renderers=[r_cool_c, r_cool_l],
                  tooltips=[("T", "@x"), ("Cooling X", "@y")])
    )

    p.grid.grid_line_color = "lightgray"
    p.outline_line_color = "black"
    p.background_fill_color = "white"
    p.legend.location = "top_left"

    figs = [p]

    if plot_derivative:
        p_dx = figure(
            title=f"{title} – dX/dT",
            width=width,
            height=height,
            x_axis_label=f"Temperature (°{temp_unit})",
            y_axis_label="dX/dT",
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )
        dx_w = np.gradient(swX, swT)
        dx_c = np.gradient(scX, scT)
        r_dx_w = p_dx.line(
            swT, dx_w, legend_label="Heating – dX/dT",
            line_width=2, color="red"
        )
        r_dx_c = p_dx.line(
            scT, dx_c, legend_label="Cooling – dX/dT",
            line_width=2, color="blue"
        )
        p_dx.add_tools(
            HoverTool(renderers=[r_dx_w],
                      tooltips=[("T", "@x"), ("dX/dT (heat)", "@y")])
        )
        p_dx.add_tools(
            HoverTool(renderers=[r_dx_c],
                      tooltips=[("T", "@x"), ("dX/dT (cool)", "@y")])
        )
        p_dx.grid.grid_line_color = "lightgray"
        p_dx.outline_line_color = "black"
        p_dx.background_fill_color = "white"
        p_dx.legend.location = "top_left"
        figs.append(p_dx)

    if plot_inverse:
        p_inv = figure(
            title=f"{title} – 1/X",
            width=width,
            height=height,
            x_axis_label=f"Temperature (°{temp_unit})",
            y_axis_label="1/X",
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )
        # compute inverse safely (zeros become NaN)
        swX_arr = np.array(swX)
        scX_arr = np.array(scX)
        inv_w = np.divide(1.0, swX_arr, out=np.full_like(swX_arr, np.nan), where=swX_arr != 0.0)
        inv_c = np.divide(1.0, scX_arr, out=np.full_like(scX_arr, np.nan), where=scX_arr != 0.0)

        # mask to finite values only
        mask_w = np.isfinite(inv_w)
        mask_c = np.isfinite(inv_c)

        # plot heating inverse
        r_inv_w = p_inv.line(
            np.array(swT)[mask_w],
            inv_w[mask_w],
            legend_label="Heating – 1/X",
            line_width=2, color="red",
        )

        # plot cooling inverse
        r_inv_c = p_inv.line(
            np.array(scT)[mask_c],
            inv_c[mask_c],
            legend_label="Cooling – 1/X",
            line_width=2, color="blue",
        )

        p_inv.add_tools(
            HoverTool(renderers=[r_inv_w],
                      tooltips=[("T", "@x"), ("1/X (heat)", "@y")])
        )
        p_inv.add_tools(
            HoverTool(renderers=[r_inv_c],
                      tooltips=[("T", "@x"), ("1/X (cool)", "@y")])
        )
        p_inv.grid.grid_line_color = "lightgray"
        p_inv.outline_line_color = "black"
        p_inv.background_fill_color = "white"
        p_inv.legend.location = "top_left"
        figs.append(p_inv)

    for fig in figs:
        show(fig)

    if return_figure:
        return tuple(figs)
    return None


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
        # loess smoothing
        spl = lowess(experiment['magn_mass_shift'], experiment['log_dc_field'], frac=smooth_frac)
        experiment['smoothed_magn_mass_shift'] = spl[:, 1]
        experiment['smoothed_log_dc_field'] = spl[:, 0]
    return experiment, Bcr
    
def plot_backfield_data(
    experiment,
    field="treat_dc_field",
    magnetization="magn_mass",
    figsize=(5, 12),
    plot_raw=True,
    plot_processed=True,
    plot_spectrum=True,
    interactive=False,
    return_figure=True,
    show_plot=True,
):
    """
    Plot backfield data: raw, processed, and coercivity spectrum.

    Data processing steps:
      - Raw: magnetization vs. field (T).
      - Processed: magn_mass_shift = magn_mass − min(magn_mass);
        log_dc_field = log10(−field·1e3) (log10 mT axis).
      - Spectrum: derivative −ΔM/Δ(log B).

    Parameters
    ----------
    experiment : DataFrame
        Must contain raw and, if requested, processed columns.
    plot_raw : bool
    plot_processed : bool
    plot_spectrum : bool
    interactive : bool
    return_figure : bool
    show_plot : bool

    Returns
    -------
    Matplotlib (fig, axes) or Bokeh grid or None
    """
    # check columns
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

    # prepare spectrum
    if plot_spectrum:
        log_b = experiment["log_dc_field"]
        shift_m = experiment["magn_mass_shift"]
        raw_dy = -np.diff(shift_m) / np.diff(log_b)
        raw_dx_log = log_b.rolling(2).mean().dropna()
        smooth_dy = -np.diff(experiment["smoothed_magn_mass_shift"]) / np.diff(
            experiment["smoothed_log_dc_field"]
        )
        smooth_dx_log = experiment["smoothed_log_dc_field"].rolling(2).mean().dropna()
        # axis: convert log10(mT) → mT for plotting, but axis scale remains log
        raw_dx = 10**raw_dx_log
        smooth_dx = 10**smooth_dx_log

    if interactive:
        tools = [
            HoverTool(tooltips=[("Field (mT)", "@x"), ("Mag", "@y")]),
            "pan,box_zoom,reset"
        ]
        figs = []
        palette = Category10[3]

        if plot_raw:
            p0 = figure(
                title="Raw backfield",
                x_axis_label="Field (T)",
                y_axis_label="Magnetization",
                tools=tools,
                sizing_mode="stretch_width",
                height = figsize[1]*25,
            )
            p0.scatter(
                experiment[field],
                experiment[magnetization],
                legend_label="raw",
                color=palette[0],
                size=6,
            )
            p0.line(experiment[field], experiment[magnetization], color=palette[0])
            p0.legend.click_policy = "hide"
            figs.append(p0)

        if plot_processed:
            x_shifted = 10 ** experiment["log_dc_field"]
            x_smooth = 10 ** experiment["smoothed_log_dc_field"]
            p1 = figure(
                title="Processed backfield",
                x_axis_label="Field (mT)",
                y_axis_label="Magnetization",
                x_axis_type="log",
                tools=tools,
                sizing_mode="stretch_width",
                height = figsize[1]*25,
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
            p1.legend.click_policy = "hide"
            figs.append(p1)

        if plot_spectrum:
            p2 = figure(
                title="Coercivity spectrum",
                x_axis_label="Field (mT)",
                y_axis_label="dM/dB",
                x_axis_type="log",
                tools=tools,
                sizing_mode="stretch_width",
                height = figsize[1]*25,
            )
            p2.scatter(raw_dx, raw_dy, legend_label="raw spectrum",
                       color=palette[2], size=6)
            p2.line(smooth_dx, smooth_dy, color=palette[2],
                    legend_label="smoothed spectrum")
            p2.legend.click_policy = "hide"
            figs.append(p2)

        grid = gridplot(figs, ncols=1, sizing_mode="stretch_width")
        if show_plot:
            show(grid)
        if return_figure:
            return grid
        return None

    # static Matplotlib
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
            ax.set(title="raw backfield", xlabel="field (T)", ylabel="magnetization")
            ax.legend()
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
                title="processed", xlabel="field (mT)", ylabel="magnetization"
            )
            ax.legend()
        else:  # spectrum
            ax.scatter(raw_dx_log, raw_dy, c="gray", s=10, label="raw spectrum")
            ax.plot(smooth_dx_log, smooth_dy, c="k", label="smoothed spectrum")
            ticks = ax.get_xticks()
            ax.set_xticklabels([f"{round(10**t, 1)}" for t in ticks])
            ax.set(title="spectrum", xlabel="field (mT)", ylabel="dM/dB")
            ax.legend()

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

    assert n_comps > 0, 'n_component must be greater than 0'
    assert isinstance(n_comps, int), 'n_component must be an integer'
    assert isinstance(parameters, pd.DataFrame), f"Expected a pandas DataFrame, but got {type(parameters).__name__}"
    assert n_comps == parameters.shape[0], 'number of components must match the number of rows in the parameters table'
    assert n_iter > 0, 'n_iter must be greater than 0'

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
        if skewed == False:
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
    ax.set_ylabel('dM/dB', fontsize=14)
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
        ax.set_ylabel('dM/dB', fontsize=12)

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

        fig.canvas.draw()
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

def backfield_MaxUnmix(field, magnetization, n_comps=1, parameters=None, skewed=True, n_resample=100, proportion=0.95, figsize=(10, 6)):
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
    '''

    assert len(parameters) == n_comps, f"Number of rows in parameters ({len(parameters)}) should be equal to n_comps ({n_comps})"
    assert proportion > 0 and proportion <= 1, f"proportion should be between 0 and 1, but got {proportion}"
    assert parameters is not None, f"parameters should not be None"

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
        index_resample = np.random.choice(len(B), size=int(len(B) * proportion), replace=True)
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
            if skewed == False:
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

    # calculate the mean and std of the parameters
    mean_parameters = np.mean(all_parameters, axis=0)
    std_parameters = np.std(all_parameters, axis=0)

    # report a dictionary of the mean and std of the parameters
    parameters_dict = {}
    for i in range(n_comps):
        this_parameters_dict = {
            f'g{i+1}_amplitude': mean_parameters[i][0],
            f'g{i+1}_center': 10**mean_parameters[i][1],
            f'g{i+1}_sigma': 10**mean_parameters[i][2],
            f'g{i+1}_gamma': mean_parameters[i][3],
            f'g{i+1}_amplitude_std': std_parameters[i][0],
            f'g{i+1}_center_std': 10**std_parameters[i][1],
            f'g{i+1}_sigma_std': 10**std_parameters[i][2],
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
    ax.set_ylabel('dM/dB', fontsize=12)
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
    # check if the description cell is type string
    if isinstance(specimens_df[specimens_df['experiments'] == experiment_name]['description'].iloc[0], str):
        # unpack the string to a dict, then add the new stats, then pack it back to a string
        description_dict = eval(specimens_df[specimens_df['experiments'] == experiment_name]['description'].iloc[0])
        for key in unmix_result_dict:
            if key in description_dict:
                # if the key already exists, update it
                description_dict[key] = unmix_result_dict[key]
            else:
                # if the key does not exist, add it
                description_dict[key] = unmix_result_dict[key]
        # pack the dict back to a string
        specimens_df.loc[specimens_df['experiments'] == experiment_name, 'description'] = str(description_dict)
    else:
        # if not, create a new dict
        specimens_df.loc[specimens_df['experiments'] == experiment_name, 'description'] = str(unmix_result_dict)
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


# Day plot function
# ------------------------------------------------------------------------------------------------------------------
def day_plot_MagIC(specimen_data, 
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

    ax = day_plot(Mr = summary_sats[Mr],
                       Ms = summary_sats[Ms],
                       Bcr = summary_sats[Bcr],
                       Bc = summary_sats[Bc], 
                       **kwargs)
    return ax
    
def day_plot(Mr, Ms, Bcr, Bc, 
             Mr_Ms_lower=0.05, Mr_Ms_upper=0.5, Bc_Bcr_lower=1.5, Bc_Bcr_upper=4, 
             plot_day_lines = True, 
             plot_MD_slope=True,
             plot_SP_SD_mixing=[10, 15, 25, 30],
             plot_SD_MD_mixing=True,
             color='black', marker='o', 
             label = 'sample', alpha=1, 
             lc='black', lw=0.5, 
             legend=True, figsize=(8,6)):
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

    Returns
    -------
    ax : matplotlib.axes._axes.Axes
        the axes object of the plot.

    '''
    # force numpy arrays
    Ms = np.asarray(Ms)
    Mr = np.asarray(Mr)
    Bc = np.asarray(Bc)
    Bcr = np.asarray(Bcr)
    Bcr_Bc = Bcr/Bc
    Mr_Ms = Mr/Ms
    _, ax = plt.subplots(figsize = figsize)
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
    ax.set_xlabel('Bcr/Bc', fontsize=12)
    ax.set_ylabel('Mr/Ms', fontsize=12)
    ax.set_title('Day plot', fontsize=14)

    if legend:
        ax.legend(loc='lower right', fontsize=10)
    return ax

def squareness_Bc(Ms, Mr, Bc, color = 'black', marker = 'o', label = 'sample', alpha=1, lc = 'black', lw=0.5, legend=True, figsize = (6,6)):
    '''
    fuction for making squareness coercivity plot
        plots Mr/Ms vs Bc
    '''
    # force numpy arrays
    Ms = np.asarray(Ms)
    Mr = np.asarray(Mr)
    Bc = np.asarray(Bc)
    Mr_Ms = Mr/Ms
    _, ax = plt.subplots(figsize = figsize)
    ax.scatter(Bc, Mr_Ms, color = color, marker = marker, label = label, alpha=alpha, zorder = 100)

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
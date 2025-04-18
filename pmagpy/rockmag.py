import pandas as pd
import numpy as np
import copy

from scipy.optimize import minimize, brent, least_squares, minimize_scalar
from scipy.signal import savgol_filter

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patches as patches

try:
    import ipywidgets as widgets
    from IPython.display import display
except ImportError:
    widgets = None
    display = None

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    go = None
    make_subplots = None
try:

    from bokeh.plotting import figure, show
except ImportError:
    raise ImportError("Bokeh is not installed. Please install it to enable hysteresis data processing.")

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

# general I/O functions
# ------------------------------------------------------------------------------------------------------------------

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


def get_plotly_marker(matplotlib_marker):
    """
    Maps a Matplotlib marker style to its Plotly equivalent.

    Parameters:
        matplotlib_marker (str): A marker style in Matplotlib format.

    Returns:
        str: Corresponding marker style in Plotly format.
    """
    marker_dict = {
        '.': 'circle',
        'o': 'circle',
        '^': 'triangle-up',
        's': 'square',
        '*': 'star',
        '+': 'cross',
        'x': 'x',
        'D': 'diamond',
        '|': 'line-ns',
        '_': 'line-ew',
    }
    return marker_dict.get(matplotlib_marker, 'circle')  # Default to 'circle' if not found


def plot_mpms_dc(fc_data=None, zfc_data=None, rtsirm_cool_data=None, rtsirm_warm_data=None, 
                   fc_color='#1f77b4', zfc_color='#ff7f0e', rtsirm_cool_color='#17becf', rtsirm_warm_color='#d62728',
                   fc_marker='d', zfc_marker='p', rtsirm_cool_marker='s', rtsirm_warm_marker='o',
                   symbol_size=4, use_plotly=False, plot_derivative=False, return_figure=False,
                   show_plot=True, drop_first=False, drop_last=False):
    """
    Plots MPMS data and optionally its derivatives for Field Cooled, Zero Field Cooled,
    RTSIRM Cooling, and RTSIRM Warming using either Matplotlib or Plotly.
    
    Each of the datasets is optional; only the ones provided will be plotted.
    
    Parameters:
        fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data (DataFrame or None): DataFrames containing the MPMS data.
        fc_color, zfc_color, rtsirm_cool_color, rtsirm_warm_color (str): HEX color codes for each plot.
        fc_marker, zfc_marker, rtsirm_cool_marker, rtsirm_warm_marker (str): Marker symbols for each plot.
        symbol_size (int): Size of the markers in matplotlib; symbol size in Plotly is fixed.
        use_plotly (bool): If True, uses Plotly for plotting. Otherwise, uses Matplotlib.
        plot_derivative (bool): If True, plots the derivative of the magnetization data (for each provided dataset).
        drop_first (bool): If True, drops the first row of each provided dataframe.
        drop_last (bool): If True, drops the last row of each provided dataframe.
        
    Returns:
        fig: The matplotlib.figure.Figure object containing the plot (only when using Matplotlib).
    """
    # Conditionally drop first/last rows for each dataset
    if drop_first:
        if fc_data is not None:
            fc_data = fc_data[1:]
        if zfc_data is not None:
            zfc_data = zfc_data[1:]
        if rtsirm_cool_data is not None:
            rtsirm_cool_data = rtsirm_cool_data[1:]
        if rtsirm_warm_data is not None:
            rtsirm_warm_data = rtsirm_warm_data[1:]
        
    if drop_last:
        if fc_data is not None:
            fc_data = fc_data[:-1]
        if zfc_data is not None:
            zfc_data = zfc_data[:-1]
        if rtsirm_cool_data is not None:
            rtsirm_cool_data = rtsirm_cool_data[:-1]
        if rtsirm_warm_data is not None:
            rtsirm_warm_data = rtsirm_warm_data[:-1]
        
    # Calculate derivatives only for the datasets that are provided
    if plot_derivative:
        fc_derivative = thermomag_derivative(fc_data['meas_temp'], fc_data['magn_mass']) if fc_data is not None else None
        zfc_derivative = thermomag_derivative(zfc_data['meas_temp'], zfc_data['magn_mass']) if zfc_data is not None else None
        rtsirm_cool_derivative = thermomag_derivative(rtsirm_cool_data['meas_temp'], rtsirm_cool_data['magn_mass']) if rtsirm_cool_data is not None else None
        rtsirm_warm_derivative = thermomag_derivative(rtsirm_warm_data['meas_temp'], rtsirm_warm_data['magn_mass']) if rtsirm_warm_data is not None else None

    if use_plotly:
        rows, cols = (2, 2) if plot_derivative else (1, 2)
        fig = make_subplots(rows=rows, cols=cols)
        
        # Add original data traces conditionally
        if fc_data is not None:
            fig.add_trace(go.Scatter(x=fc_data['meas_temp'], y=fc_data['magn_mass'], mode='markers+lines',
                                     name='FC', marker=dict(color=fc_color)), row=1, col=1)
        if zfc_data is not None:
            fig.add_trace(go.Scatter(x=zfc_data['meas_temp'], y=zfc_data['magn_mass'], mode='markers+lines',
                                     name='ZFC', marker=dict(color=zfc_color)), row=1, col=1)
        if rtsirm_cool_data is not None:
            fig.add_trace(go.Scatter(x=rtsirm_cool_data['meas_temp'], y=rtsirm_cool_data['magn_mass'],
                                     mode='markers+lines', name='RTSIRM Cooling', marker=dict(color=rtsirm_cool_color)),
                                     row=1, col=2)
        if rtsirm_warm_data is not None:
            fig.add_trace(go.Scatter(x=rtsirm_warm_data['meas_temp'], y=rtsirm_warm_data['magn_mass'],
                                     mode='markers+lines', name='RTSIRM Warming', marker=dict(color=rtsirm_warm_color)),
                                     row=1, col=2)

        # Add derivative data traces if required and available
        if plot_derivative:
            if fc_derivative is not None:
                fig.add_trace(go.Scatter(x=fc_derivative['T'], y=fc_derivative['dM_dT'], mode='markers+lines', 
                                    name='FC Derivative', marker=dict(color=fc_color, symbol=get_plotly_marker(fc_marker))),
                                    row=2, col=1)
            if zfc_derivative is not None:
                fig.add_trace(go.Scatter(x=zfc_derivative['T'], y=zfc_derivative['dM_dT'], mode='markers+lines', 
                                    name='ZFC Derivative', marker=dict(color=zfc_color, symbol=get_plotly_marker(zfc_marker))),
                                    row=2, col=1)
            if rtsirm_cool_derivative is not None:
                fig.add_trace(go.Scatter(x=rtsirm_cool_derivative['T'], y=rtsirm_cool_derivative['dM_dT'], mode='markers+lines', 
                                    name='RTSIRM Cooling Derivative', marker=dict(color=rtsirm_cool_color, symbol=get_plotly_marker(rtsirm_cool_marker))),
                                    row=2, col=2)
            if rtsirm_warm_derivative is not None:
                fig.add_trace(go.Scatter(x=rtsirm_warm_derivative['T'], y=rtsirm_warm_derivative['dM_dT'], mode='markers+lines', 
                                    name='RTSIRM Warming Derivative', marker=dict(color=rtsirm_warm_color, symbol=get_plotly_marker(rtsirm_warm_marker))),
                                    row=2, col=2)
        
        # Update axis titles and layout
        fig.update_yaxes(title_text="M (Am2/kg)", row=1, col=1)
        fig.update_yaxes(title_text="M (Am2/kg)", row=1, col=2)
        if plot_derivative:
            fig.update_yaxes(title_text="dM/dT", row=2, col=1)
            fig.update_yaxes(title_text="dM/dT", row=2, col=2)
            fig.update_xaxes(title_text="T (K)", row=2, col=1)
            fig.update_xaxes(title_text="T (K)", row=2, col=2)
            fig.update_layout(height=900)
        else:
            fig.update_xaxes(title_text="T (K)", row=1, col=2)
            fig.update_layout(height=450)

        fig.update_xaxes(title_text="T (K)", row=1, col=1)
        fig.update_layout(title="MPMS Data and Derivatives" if plot_derivative else "MPMS Data")
        fig.show()
            
    else:
        # Matplotlib plotting
        if plot_derivative:
            fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(9, 6))
        else:
            fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(9, 3))
            
        # Plot original data conditionally
        if not plot_derivative:
            if fc_data is not None:
                axs[0].plot(fc_data['meas_temp'], fc_data['magn_mass'], color=fc_color, marker=fc_marker,
                            linestyle='-', markersize=symbol_size, label='FC')
            if zfc_data is not None:
                axs[0].plot(zfc_data['meas_temp'], zfc_data['magn_mass'], color=zfc_color, marker=zfc_marker,
                            linestyle='-', markersize=symbol_size, label='ZFC')
            if rtsirm_cool_data is not None:
                axs[1].plot(rtsirm_cool_data['meas_temp'], rtsirm_cool_data['magn_mass'], color=rtsirm_cool_color,
                            marker=rtsirm_cool_marker, linestyle='-', markersize=symbol_size, label='RTSIRM Cooling')
            if rtsirm_warm_data is not None:
                axs[1].plot(rtsirm_warm_data['meas_temp'], rtsirm_warm_data['magn_mass'], color=rtsirm_warm_color,
                            marker=rtsirm_warm_marker, linestyle='-', markersize=symbol_size, label='RTSIRM Warming')
            for ax in axs:
                ax.set_xlabel("Temperature (K)")
                ax.set_ylabel("Magnetization (Am$^2$/kg)")
                ax.legend()
                ax.grid(True)
                ax.set_xlim(0,300)
        
        elif plot_derivative:
            if fc_data is not None:
                axs[0,0].plot(fc_data['meas_temp'], fc_data['magn_mass'], color=fc_color, marker=fc_marker,
                               linestyle='-', markersize=symbol_size, label='FC')
            if zfc_data is not None:
                axs[0,0].plot(zfc_data['meas_temp'], zfc_data['magn_mass'], color=zfc_color, marker=zfc_marker,
                               linestyle='-', markersize=symbol_size, label='ZFC')
            if rtsirm_cool_data is not None:
                axs[0,1].plot(rtsirm_cool_data['meas_temp'], rtsirm_cool_data['magn_mass'], color=rtsirm_cool_color, marker=rtsirm_cool_marker,
                               linestyle='-', markersize=symbol_size, label='RTSIRM Cooling')
            if rtsirm_warm_data is not None:
                axs[0,1].plot(rtsirm_warm_data['meas_temp'], rtsirm_warm_data['magn_mass'], color=rtsirm_warm_color, marker=rtsirm_warm_marker,
                               linestyle='-', markersize=symbol_size, label='RTSIRM Warming')
            for ax in axs[0,:]:
                ax.set_xlabel("Temperature (K)")
                ax.set_ylabel("Magnetization (Am$^2$/kg)")
                ax.legend()
                ax.grid(True)
                ax.set_xlim(0,300)
                
            if plot_derivative:
                if fc_derivative is not None:
                    axs[1,0].plot(fc_derivative['T'], fc_derivative['dM_dT'], marker=fc_marker, linestyle='-', color=fc_color,
                                   markersize=symbol_size, label='FC Derivative')
                if zfc_derivative is not None:
                    axs[1,0].plot(zfc_derivative['T'], zfc_derivative['dM_dT'], marker=zfc_marker, linestyle='-', color=zfc_color,
                                   markersize=symbol_size, label='ZFC Derivative')
                if rtsirm_cool_derivative is not None:
                    axs[1,1].plot(rtsirm_cool_derivative['T'], rtsirm_cool_derivative['dM_dT'], marker=rtsirm_cool_marker, linestyle='-', color=rtsirm_cool_color,
                                   markersize=symbol_size, label='RTSIRM Cooling Derivative')
                if rtsirm_warm_derivative is not None:
                    axs[1,1].plot(rtsirm_warm_derivative['T'], rtsirm_warm_derivative['dM_dT'], marker=rtsirm_warm_marker, linestyle='-', color=rtsirm_warm_color,
                                   markersize=symbol_size, label='RTSIRM Warming Derivative')
                for ax in axs[1,:]:
                    ax.set_xlabel("Temperature (K)")
                    ax.set_ylabel("dM/dT")
                    ax.legend()
                    ax.grid(True)
                    ax.set_xlim(0,300)

        fig.tight_layout()
        
        if show_plot:
            plt.show()
        
        if return_figure:
            return fig


def make_mpms_plots_dc(measurements):
    """
    Create a UI for specimen selection and dynamically update MPMS plots based on the selected
    specimen and plot library choice. This version adds event handlers to ensure updates occur
    upon initial selection.

    Parameters:
    experiments : pandas.DataFrame
        The dataframe containing experiment data with columns including 'specimen' and 'method_codes'.
    measurements : pandas.DataFrame
        The dataframe containing measurement data used for plotting MPMS data.
    """
    # Filter to get specimens with desired method codes
    experiments = measurements.groupby(['specimen', 'method_codes']).size().reset_index().iloc[:, :2]
    filtered_experiments = experiments[experiments['method_codes'].isin(['LP-FC', 'LP-ZFC'])]
    specimen_options = filtered_experiments['specimen'].unique().tolist()

    # Dropdown for specimen selection
    specimen_dropdown = widgets.Dropdown(
        options=specimen_options,
        description='Specimen:',
        value=specimen_options[0]
    )

    # Radio buttons for plot library choice
    plot_choice = widgets.RadioButtons(
        options=[('matplotlib', False), ('plotly', True)],
        description='Plot with:',
        disabled=False
    )

    # Interactive output container
    out = widgets.Output()

    def update_mpms_plots_dc(specimen_name, use_plotly):
        """
        Update MPMS plots based on the selected specimen and plotting library choice.
        """
        with out:
            out.clear_output(wait=True)
            fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data = extract_mpms_data_dc(measurements, specimen_name)
            plot_mpms_dc(fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data, use_plotly=use_plotly, plot_derivative=True)

    def on_specimen_change(change):
        update_mpms_plots_dc(change['new'], plot_choice.value)

    def on_plot_choice_change(change):
        update_mpms_plots_dc(specimen_dropdown.value, change['new'])

    specimen_dropdown.observe(on_specimen_change, names='value')
    plot_choice.observe(on_plot_choice_change, names='value')

    # Initial plot to ensure something is displayed right away
    update_mpms_plots_dc(specimen_dropdown.value, plot_choice.value)

    # Display UI components
    display(specimen_dropdown, plot_choice, out)


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
    
    verwey_estimate = zero_crossing(temps_dM_dT_background, mgt_dM_dT, 
                                    make_plot=plot_zero_crossing, 
                                    xlim=(excluded_t_min, excluded_t_max),
                                    verwey_marker=verwey_marker, verwey_color=verwey_color,
                                    verwey_size=verwey_size)
    
    remanence_loss = np.trapz(mgt_dM_dT, temps_dM_dT_background)
    
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

    # Determine a fixed width for the descriptions to align the sliders
    description_width = '250px'  # Adjust this based on the longest description
    slider_total_width = '600px'  # Total width of the slider widget including the description

    description_style = {'description_width': description_width}
    slider_layout = widgets.Layout(width=slider_total_width)  # Set the total width of the slider widget

    # Update sliders to use IntRangeSlider
    background_temp_range_slider = widgets.IntRangeSlider(
        value=[60, 250], min=0, max=300, step=1,
        description='Background Temperature Range (K):',
        layout=slider_layout, style=description_style
    )

    excluded_temp_range_slider = widgets.IntRangeSlider(
        value=[75, 150], min=0, max=300, step=1,
        description='Excluded Temperature Range (K):',
        layout=slider_layout, style=description_style
    )

    poly_deg_slider = widgets.IntSlider(
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
    
    title_label = widgets.Label(value='Adjust Parameters for ' + selected_specimen_name + ' ' + selected_method + ' fit')

    # Add the reset button to the UI
    ui = widgets.VBox([ 
        title_label,
        background_temp_range_slider, 
        excluded_temp_range_slider, 
        poly_deg_slider,
        reset_button
    ])

    out = widgets.interactive_output(
        lambda background_temp_range, excluded_temp_range, poly_deg: verwey_estimate(
            temps, mags, 
            background_temp_range[0], background_temp_range[1], 
            excluded_temp_range[0], excluded_temp_range[1], 
            poly_deg
        ), {
            'background_temp_range': background_temp_range_slider,
            'excluded_temp_range': excluded_temp_range_slider,
            'poly_deg': poly_deg_slider,
        }
    )

    out.layout.height = '500px'

    display(ui, out)


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
    
    max_dM_dT_temp = dM_dT_temps[dM_dT.idxmax()]
    
    d2M_dT2 = thermomag_derivative(dM_dT_temps, dM_dT)
    d2M_dT2_T_array = d2M_dT2['T'].to_numpy()
    max_index = np.searchsorted(d2M_dT2_T_array, max_dM_dT_temp)

    d2M_dT2_T_before = d2M_dT2['T'][max_index-1]
    d2M_dT2_before = d2M_dT2['dM_dT'][max_index-1]
    d2M_dT2_T_after = d2M_dT2['T'][max_index]
    d2M_dT2_after = d2M_dT2['dM_dT'][max_index]

    zero_cross_temp = d2M_dT2_T_before + ((d2M_dT2_T_after - d2M_dT2_T_before) / (d2M_dT2_after - d2M_dT2_before)) * (0 - d2M_dT2_before)

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

def plot_hyst_data(hyst_data,
                   hyst_color='#1f77b4',
                   hyst_marker=None,
                   symbol_size=5, use_plotly=False, return_figure=False):
    """
    Plots hysteresis data using either Matplotlib or Plotly.

    Parameters:
        hyst_data (DataFrame): DataFrames containing the hysteresis data.
        hyst_color: HEX color codes for each plot.
        hyst_marker (str): Marker symbols for each plot.
        symbol_size (int): Size of the markers in matplotlib, symbol size in plotly is fixed.
        use_plotly (bool): If True, uses Plotly for plotting. Otherwise, uses Matplotlib.
        
    Returns:
        fig: The matplotlib.figure.Figure object containing the plot (only when using Matplotlib).
    """

    if use_plotly:
        rows, cols = (1, 1)
        fig = make_subplots(rows=rows, cols=cols)
        
        # Add original data traces
        fig.add_trace(go.Scatter(x=hyst_data['meas_field_dc'], y=hyst_data['magn_mass'], mode='markers+lines', name='Hyst', marker=dict(color=hyst_color)), row=1,    col=1)
        
        # Update layout and axis titles
        # Set y-axis label for the first row to 'M (Am2/kg)'
        fig.update_yaxes(title_text="M (Am2/kg)", row=1, col=1)
        fig.update_yaxes(title_text="M (Am2/kg)", row=1, col=2)

        fig.update_xaxes(title_text="Field (Tesla)", row=1, col=1)


        fig.update_layout(title="Hysteresis Data")
        
        fig.show()
            
    else:
        # Matplotlib plotting
        fig, axs = plt.subplots(figsize=(8, 6))
            
        # Plot original data

        axs.plot(hyst_data['meas_field_dc'], hyst_data['magn_mass'], color=hyst_color, marker=hyst_marker, linestyle='-', linewidth=0.5, markersize=symbol_size, label='Loop')

        axs.set_xlabel("Field (Tesla)")
        axs.set_ylabel("Magnetization (Am$^2$/kg)")
        axs.legend()
        axs.grid(True)

        fig.tight_layout()
        plt.show()
        
        if return_figure:
            return fig
           
def make_hyst_plots(measurements):
    """
    Create a UI for specimen selection and dynamically update Hysteresis loop plots based on the selected
    specimen and plot library choice. This version adds event handlers to ensure updates occur
    upon initial selection.

    Parameters:
    experiments : pandas.DataFrame
        The dataframe containing experiment data with columns including 'specimen' and 'method_codes'.
    measurements : pandas.DataFrame
        The dataframe containing measurement data used for plotting Hysteresis loop data.
    """
    # Filter to get specimens with desired method codes
    experiments = measurements.groupby(['specimen', 'method_codes']).size().reset_index().iloc[:, :2]
    filtered_experiments = experiments[experiments['method_codes'].isin(['LP-HYS',])]
    specimen_options = filtered_experiments['specimen'].unique().tolist()

    # Dropdown for specimen selection
    specimen_dropdown = widgets.Dropdown(
        options=specimen_options,
        description='Specimen:',
        value=specimen_options[0]
    )

    # Radio buttons for plot library choice
    plot_choice = widgets.RadioButtons(
        options=[('matplotlib', False), ('plotly', True)],
        description='Plot with:',
        disabled=False
    )

    # Interactive output container
    out = widgets.Output()

    def update_hyst_plots(specimen_name, use_plotly):
        """
        Update hysteresis loop based on the selected specimen and plotting library choice.
        """
        with out:
            out.clear_output(wait=True)
            hyst_data = extract_hysteresis_data(measurements, specimen_name)
            plot_hyst_data(hyst_data, use_plotly=use_plotly)

    def on_specimen_change(change):
        update_hyst_plots(change['new'], plot_choice.value)

    def on_plot_choice_change(change):
        update_hyst_plots(specimen_dropdown.value, change['new'])

    specimen_dropdown.observe(on_specimen_change, names='value')
    plot_choice.observe(on_plot_choice_change, names='value')

    # Initial plot to ensure something is displayed right away
    update_hyst_plots(specimen_dropdown.value, plot_choice.value)

    # Display UI components
    display(specimen_dropdown, plot_choice, out)

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
    
    show(p)
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

    results = {'SST':SST, 
            'SSR':SSR,
            'SSD':SSD,
            'R_squared': R_squared, 
            'SSPE':SSPE,
            'SSLF':SSLF, 
            'MSPE':MSPE,
            'MSLF':MSLF,
            'MSR':MSR, 
            'MSD':MSD, 
            'MSPE':MSPE, 
            'MSLF':MSLF, 
            'FL':FL, 'FNL':FNL, 
            'slope':slope, 'intercept':intercept, 
            'loop is linear':FNL < 1.25}

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
    ss_res = np.sum((yarr - y_pred)**2)

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
        return -result['r2']
    
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
                'opt_H_offset':H_offset/2, 
                'opt_M_offset':M_offset, 
                'R_squared':R_squared, 'M_sn':M_sn, 'Q':Q}
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

def calc_Mrh_Mih(grid_field, grid_magnetization):
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
    # make sure the x values for the branches are exactly the same
    assert np.all(upper_branch[0] == lower_branch[0]), 'Field values for the upper and lower branches are not the same'
    
    Mrh = (upper_branch[1] - lower_branch[1])/2
    Mih = (upper_branch[1] + lower_branch[1])/2
    Me = upper_branch[1] + lower_branch[1][::-1]

    H = upper_branch[0]
    
    Mr = np.interp(0, H, Mrh)
    # Brh is the median field of Mrh
    pos_H = H[np.where(H >= 0)]
    pos_Mrh = Mrh[np.where(H >= 0)]
    neg_H = H[np.where(H < 0)]
    neg_Mrh = Mrh[np.where(H < 0)]
    Brh_pos = np.interp(Mr/2, pos_Mrh[::-1], pos_H[::-1])
    Brh_neg = np.interp(Mr/2, neg_Mrh, neg_H)
    Brh = (np.abs(Brh_pos) + np.abs(Brh_neg))/2

    return H, Mrh, Mih, Me, Brh

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
    results = {'FNL60':FNL60, 'FNL70':FNL70, 'FNL80':FNL80, 'saturation_cutoff':saturation_cutoff, 'loop is saturated':(saturation_cutoff != 0.92)}

    return results

def loop_close_test(H, Mrh, HF_cutoff=0.8):
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

    results = {'SNR':SNR, 'HAR':HAR, 'loop_is_closed':loop_is_closed}
    return results


def process_hyst_loop(field,magnetization, drift_correction=False):
    # first grid the data into symmetric field values
    grid_fields, grid_magnetizations = grid_hysteresis_loop(field, magnetization)

    if drift_correction:
        # if drift correction, by default we apply a prorated drift correction algorithm
        corrected_magnetizations = prorated_drift_correction(grid_fields, grid_magnetizations)
        grid_magnetizations = corrected_magnetizations

    pos_max_mags = grid_magnetizations[np.where(grid_fields == np.max(grid_fields))]
    neg_max_mags = grid_magnetizations[np.where(grid_fields == np.min(grid_fields))]
    if (np.abs(np.diff(pos_max_mags)/2/np.mean(pos_max_mags))>0.001) or np.abs((np.diff(neg_max_mags)/2/np.mean(neg_max_mags))>0.001):
        print('check loop drift!')

    # then perform linearity test on the whole loop (to determine wether the specimen is dominated by paramagnetic or diamagnetic signal)
    linearity_test_results = hyst_linearity_test(grid_fields, grid_magnetizations)
    if linearity_test_results['loop is linear']:
        print('raw data is linear')
    else:
        print('raw data is not linear')
    print('FNL: ', round(linearity_test_results['FNL'],2))

    if linearity_test_results['loop is linear']:
        return grid_fields, grid_magnetizations, linearity_test_results
    
    # if the loop is not linear, we need to first center the loop
    loop_centering_results = hyst_loop_centering(grid_fields, grid_magnetizations)

    print('loop centering results: field offset = {} T'.format(round(loop_centering_results['opt_H_offset'],4)), 'magnetization offset = {} Am^2/kg'.format(round(loop_centering_results['opt_M_offset'], 4)))
    print('centered raw loop Q value:', round(loop_centering_results['Q'], 2))

    grid_fields_centered = grid_fields - loop_centering_results['opt_H_offset']
    grid_magnetizations_centered = grid_magnetizations - loop_centering_results['opt_M_offset']

    # then apply default high field correction
    slope, intercept = linear_HF_fit(grid_fields_centered, grid_magnetizations_centered)
    print('apply default high field linear correction:', 'slope (X_para/dia) = {}'.format(round(slope, 4)), 'intercept (Ms) = {} Am^2/kg'.format(round(intercept, 4)))
    Ms = intercept

    grid_magnetizations_centered_HF_corrected = hyst_slope_correction(grid_fields_centered, grid_magnetizations_centered, slope)

    ferro_loop_centering_results = hyst_loop_centering(grid_fields_centered, grid_magnetizations_centered_HF_corrected)
    Qf = ferro_loop_centering_results['Q']
    print('centered ferromagnetic loop Qf value:', round(Qf, 2))

    # calculate Bc
    corrected_upper_branch, corrected_lower_branch = split_hysteresis_loop(grid_fields_centered, grid_magnetizations_centered_HF_corrected)
    upper_Bc = np.interp(0, corrected_upper_branch[1], corrected_upper_branch[0])
    lower_Bc = np.interp(0, corrected_lower_branch[1], corrected_lower_branch[0])
    Bc = (np.abs(upper_Bc) + np.abs(lower_Bc))/2

    # calculate the Mrh (remanence component), Mih (induced component), Me (error) arrays
    H, Mrh, Mih, Me, Brh = calc_Mrh_Mih(grid_fields_centered, grid_magnetizations_centered_HF_corrected)

    # check if the loop is closed
    # check_loop_closure = calc_Mrh_Mih(grid_fields, grid_magnetizations)
    loop_closure_SNR, loop_closure_HAR = loop_open_test(H, Mrh)
    if (loop_closure_SNR >=8) or (loop_closure_HAR >= -48):
        print('loop is still open!')

    print('Ms = {} Am^2/kg'.format(round(Ms, 4)))
    print('Mr = {} Am^2/kg'.format(round(Mr, 4)))
    print('Bc = {} mT'.format(round(Bc*1000, 2))) 
    print('Brh = {} mT'.format(round(Brh*1000,2)))

    # test loop saturation on the not slope-corrected data
    loop_saturation_stats = hyst_loop_saturation_test(grid_fields_centered, grid_magnetizations_centered)
    if loop_saturation_stats['FNL60'] < 2.5:
        print('loop is saturated beyond {} mT'.format(round(600*np.max(grid_fields_centered), 4)))
    elif loop_saturation_stats['FNL70'] < 2.5:
        print('loop is saturated beyond {} mT'.format(round(700*np.max(grid_fields_centered), 4)))
    elif loop_saturation_stats['FNL80'] < 2.5:
        print('loop is saturated beyond {} mT'.format(round(800*np.max(grid_fields_centered), 4)))
    else:
        print('loop is not saturated! check non-linear high field correction!')

    fig, ax =  plt.subplots(figsize=(10,10))
    ax = plot_hysteresis_loop(ax, grid_fields_centered, grid_magnetizations_centered, color='r', linewidth=1, label='centered raw data')
    ax.plot(grid_fields_centered, grid_magnetizations_centered_HF_corrected, color='b', linewidth=1, label='HF slope corrected data')
    ax.plot(H, Mrh, color='g', linewidth=1, label='Mrh')
    ax.plot(H, Mih, color='y', linewidth=1, label='Mih')
    ax.plot(H, Me, color='brown', linewidth=1, label='Me')
    plt.legend()

    results = {'grid_fields': grid_fields, 
               'grid_magnetizations': grid_magnetizations, 
               'linearity_test_results': linearity_test_results,
               'loop_centering_results': loop_centering_results,
               'ferro_loop_centering_results': ferro_loop_centering_results,
               'grid_fields_centered': grid_fields_centered, 
               'grid_magnetizations_centered': grid_magnetizations_centered, 
               'grid_magnetizations_centered_HF_corrected': grid_magnetizations_centered_HF_corrected, 
               'H': H, 'Mrh': Mrh, 'Mih': Mih, 'Me': Me, 'Ms': Ms, 'Mr': Mr, 'Bc': Bc, 'Brh': Brh,
               'loop_saturation_stats': loop_saturation_stats}

    return results, ax

def export_hyst_specimen_table(specimen_name, results):
    '''
    function to export the hysteresis data to a MagIC specimen data table
    
    Parameters
    ----------
    specimen_name : str
        name of the specimen
    results : dict
        dictionary with the hysteresis processing results
    
    Returns
    -------
    pd.DataFrame
        dataframe with the hysteresis data
    '''
    results_df = pd.DataFrame(columns=['specimen', 'Q', 'Qf', 'Ms', 'Mr', 'Bc', 'Brh', 'FNL', 'method_codes'])
    results_df.loc[0] = [specimen_name, 
                         results['loop_centering_results']['Q'], 
                         results['ferro_loop_centering_results']['Q'], 
                         results['Ms'], 
                         results['Mr'], 
                         results['Bc'], 
                         results['Brh'], 
                         results['linearity_test_results']['FNL'], 
                         'LP-HYS']
    
    return results_df

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
    function for optimizing the high field non-linear fit

    Parameters
    ----------
    H : numpy array
        field values
    M : numpy array
        magnetization values
    HF_cutoff : float
        high field cutoff percentage value
    fit_type : type of nonlinear fit
        can be 'IRM' or 'Fabian' or 'Fabian_fixed_beta'
    initial_guess : numpy array
        initial guess for the optimization
    bounds : tuple
        bounds for the optimization

    Returns
    -------
    results : scipy.optimize.OptimizeResult
        results of the optimization
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
    lin_SSD = linear_fit_ANOVA['SSD']

    # now calculate the nonlinear fit SSD
    nl_SST = np.sum((HF_magnetization - np.mean(HF_magnetization)) ** 2)

    # sum of squares due to regression
    nl_SSR = np.sum((nonlinear_fit - np.mean(HF_magnetization)) ** 2)
    
    # the remaining unexplained variation (noise and lack of fit)
    nl_SSD = nl_SST-nl_SSR

    # calculate the Fnl_lin stat
    Fnl_lin = ((lin_SSD - nl_SSD) / (4-2))/(nl_SSD / (len(HF_field) - 4))

    final_result['Fnl_lin'] = Fnl_lin
    return final_result

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


def plot_X_T(experiment,
             temperature_column='meas_temp',
             magnetic_column='susc_chi_mass',
             temp_unit='C', 
             smooth_window=0,
             remove_holder=True):
    """
    Plot the high‑temperature X–T curve, its derivative, and reciprocal.

    Parameters:
        experiment (pandas.DataFrame):
            The IRM experiment data exported into MagIC format.
        temperature_column (str, optional):
            Name of the temperature column. Defaults to 'meas_temp'.
        magnetic_column (str, optional):
            Name of the susceptibility column.
            Defaults to 'susc_chi_mass'.
        temp_unit (str, optional):
            Unit of temperature, either 'K' or 'C'. Defaults to 'C'.
        smooth_window (int, optional):
            Window size for running‑average smoothing that represents
            the temperature range over which the average is calculated. 
            Defaults to 0 (no smoothing).
        remove_holder (bool, optional):
            If True, subtract the minimum holder signal from the data.
            Defaults to True.

    Returns:
        tuple[plotly.graph_objs.Figure, plotly.graph_objs.Figure, plotly.graph_objs.Figure]:
            A 3‑tuple containing:
            - fig: Combined heating and cooling X–T plot.
            - fig_dxdt: dX/dT vs. temperature plot.
            - fig_inv: 1/X vs. temperature plot.
    """
    warm_T, warm_X, cool_T, cool_X = split_warm_cool(experiment,
                                                     temperature_column=temperature_column,
                                                     magnetic_column=magnetic_column)

    # Create a plot for the 'heat' dataset with red points and a line
    fig_heat = go.Figure()
    if temp_unit == 'C':
        warm_T = [T-273.15 for T in warm_T]
        cool_T = [T-273.15 for T in cool_T]

    else:
        raise ValueError('temp_unit must be either "K" or "C"')
    
    if remove_holder:
        # now use the min max temp range to select the holder X data
        holder_warm_X = min(warm_X)
        holder_cool_X = min(cool_X)
        warm_X = [X - holder_warm_X for X in warm_X]
        cool_X = [X - holder_cool_X for X in cool_X]

    smoothed_warm_T, smoothed_warm_X, smoothed_warm_Tvars, smoothed_warm_Xvars = X_T_running_average(warm_T, warm_X, smooth_window)
    smoothed_cool_T, smoothed_cool_X, smoothed_cool_Tvars, smoothed_cool_Xvars = X_T_running_average(cool_T, cool_X, smooth_window)

    # Add heat data as a scatter plot with red points and lines
    fig_heat.add_trace(go.Scatter(
        x=warm_T,
        y=warm_X,
        mode='markers',
        marker=dict(color='red', opacity=0.5),
        name='Heating - zero corrected'
    ))
    fig_heat.add_trace(go.Scatter(
        x=smoothed_warm_T,
        y=smoothed_warm_X,
        mode='lines',
        line=dict(color='red'),
        name='Heating - zero corrected - smoothed'
    ))
    # Create a scatter plot for the 'cooling' dataset with blue points and a line
    fig_cool = go.Figure()

    # Add cooling data as a scatter plot with blue points and lines
    fig_cool.add_trace(go.Scatter(
        x=cool_T,
        y=cool_X,
        mode='markers',
        marker=dict(color='blue', opacity=0.5),
        name='Cooling - zero corrected'
    ))
    fig_cool.add_trace(go.Scatter(
        x=smoothed_cool_T,
        y=smoothed_cool_X,
        mode='lines',
        line=dict(color='blue'),
        name='Cooling - zero corrected - smoothed'
    ))

    # Combine the two figures
    fig = go.Figure(data=fig_heat.data + fig_cool.data)

    width = 900  # Adjust the width to your preference
    height = int(width / 1.618)  # Calculate height based on the golden ratio

    # Update the layout with a unified title and labels
    fig.update_layout(
            title={
            'text': f"{experiment['specimen'].unique()[0]}",
            'x': 0.5,  # Center the title
            'xanchor': 'center'
        },
        width=width,
        height=height,
        xaxis_title=f'Temperature (&deg;{temp_unit})',
        yaxis_title='<i>k</i> (m<sup>3</sup> kg<sup>-1</sup>)',
        showlegend=True,
        paper_bgcolor='white',  # Background color of the entire plot
        plot_bgcolor='white',   # Background color of the plotting area
        font=dict(
            family='Roboto, sans-serif',
            size=18,
            color="Black"
        ),
        xaxis=dict(
            tick0=0,  # Start at 0
            dtick=100,  # Tick every 100 units
            gridcolor='lightgray',  # Color of the grid lines
            gridwidth=1,  # Width of the grid lines
            showline=True,  # Show x-axis line
            linewidth=1,  # Width of the x-axis line
            linecolor='black'  # Color of the x-axis line
        ),
        yaxis=dict(
            # Automatic tick marks on the y-axis
            autorange= True,  # Reversed for easier reading
            tickformat='.1e',  # Scientific notation format
            gridcolor='lightgray',  # Color of the grid lines
            gridwidth=1,  # Width of the grid lines
            showline=True,  # Show y-axis line
            linewidth=1,  # Width of the y-axis line
            linecolor='black'  # Color of the y-axis line
        ),
            shapes=[
            # Frame around the plot
            dict(
                type='rect',
                xref='paper', yref='paper',
                x0=0, y0=0, x1=1, y1=1,
                line=dict(color='black', width=2)
            )
        ],
        margin=dict(
            l=50,  # Adjust left margin
            r=50,  # Adjust right margin
            b=50,  # Adjust bottom margin
            t=80   # Adjust top margin for title
        )
    )

    # add a new figure below the X-T plot

    fig_dxdt = go.Figure()
    dxdt = np.gradient(smoothed_warm_X, smoothed_warm_T)
    fig_dxdt.add_trace(go.Scatter(
        x=smoothed_warm_T,
        y=dxdt,
        mode='markers+lines',
        line=dict(color='red'),
        name='Heating - dX/dT smoothed'
    ))

    dxdt = np.gradient(smoothed_cool_X, smoothed_cool_T)
    fig_dxdt.add_trace(go.Scatter(
        x=smoothed_cool_T,
        y=dxdt,
        mode='markers+lines',
        line=dict(color='blue'),
        name='Cooling - dX/dT smoothed'
    ))

    fig_dxdt.update_layout(
        title={
            'text': f"{experiment['specimen'].unique()[0]} - dX/dT",
            'x': 0.5,  # Center the title
            'xanchor': 'center'
        },
        width=width,
        height=height,
        xaxis_title=f'Temperature (&deg;{temp_unit})',
        yaxis_title='dX/dT',
        showlegend=True,
        paper_bgcolor='white',  # Background color of the entire plot
        plot_bgcolor='white',   # Background color of the plotting area
        font=dict(
            family='Roboto, sans-serif',
            size=18,
            color="Black"
        ),
        xaxis=dict(
            tick0=0,  # Start at 0
            dtick=100,  # Tick every 100 units
            gridcolor='lightgray',  # Color of the grid lines
            gridwidth=1,  # Width of the grid lines
            showline=True,  # Show x-axis line
            linewidth=1,  # Width of the x-axis line
            linecolor='black'  # Color of the x-axis line
        ),
        yaxis=dict(
            # Automatic tick marks on the y-axis
            autorange=True,  # Reversed for easier reading
            tickformat='.1e',  # Scientific notation format
            gridcolor='lightgray',  # Color of the grid lines
            gridwidth=1,  # Width of the grid lines
            showline=True,  # Show y-axis line
            linewidth=1,  # Width of the y-axis line
            linecolor='black'  # Color of the y-axis line
        ),
        shapes=[
            # Frame around the plot
            dict(
                type='rect',
                xref='paper', yref='paper',
                x0=0, y0=0, x1=1, y1=1,
                line=dict(color='black', width=2)
            )
        ],
        margin=dict(
            l=50,  # Adjust left margin
            r=50,  # Adjust right margin
            b=50,  # Adjust bottom margin
            t=80   # Adjust top margin for title
        )
    )

    # add a new figure below the X-T plot
    fig_inv = go.Figure()
    inv_warm_X = [1/X for X in smoothed_warm_X]
    inv_cool_X = [1/X for X in smoothed_cool_X]
    fig_inv.add_trace(go.Scatter(
        x=smoothed_warm_T,
        y=inv_warm_X,
        mode='markers+lines',
        line=dict(color='red'),
        name='Heating - 1/X smoothed'
    ))
    fig_inv.add_trace(go.Scatter(
        x=smoothed_cool_T,
        y=inv_cool_X,
        mode='markers+lines',
        line=dict(color='blue'),
        name='Cooling - 1/X smoothed'
    ))

    fig_inv.update_layout(
        title={
            'text': f"{experiment['specimen'].unique()[0]} - 1/X",
            'x': 0.5,  # Center the title
            'xanchor': 'center'
        },
        width=width,
        height=height,
        xaxis_title=f'Temperature (&deg;{temp_unit})',
        yaxis_title='1/X',
        showlegend=True,
        paper_bgcolor='white',  # Background color of the entire plot
        plot_bgcolor='white',   # Background color of the plotting area
        font=dict(
            family='Roboto, sans-serif',
            size=18,
            color="Black"
        ),
        xaxis=dict(
            tick0=0,  # Start at 0
            dtick=100,  # Tick every 100 units
            gridcolor='lightgray',  # Color of the grid lines
            gridwidth=1,  # Width of the grid lines
            showline=True,  # Show x-axis line
            linewidth=1,  # Width of the x-axis line
            linecolor='black'  # Color of the x-axis line
        ),
        yaxis=dict(
            # Automatic tick marks on the y-axis
            autorange=True,  # Reversed for easier reading
            tickformat='.1e',  # Scientific notation format
            gridcolor='lightgray',  # Color of the grid lines
            gridwidth=1,  # Width of the grid lines
            showline=True,  # Show y-axis line
            linewidth=1,  # Width of the y-axis line
            linecolor='black'  # Color of the y-axis line
        ),
        shapes=[
            # Frame around the plot
            dict(
                type='rect',
                xref='paper', yref='paper',
                x0=0, y0=0, x1=1, y1=1,
                line=dict(color='black', width=2)
            )
        ],
        margin=dict(
            l=50,  # Adjust left margin
            r=50,  # Adjust right margin
            b=50,  # Adjust bottom margin
            t=80   # Adjust top margin for title
        )
    )


    # display the main figure
    fig.show()

    # display and return the other two figures depending on the plot_dxdt and plot_inv
    fig_dxdt.show()
    fig_inv.show()

    return fig, fig_dxdt, fig_inv


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


def optimize_X_T_running_average_window(experiment, min_temp_window=0, max_temp_window=50, steps=50, colormapwarm='tab20b', colormapcool='tab20c'):
    warm_T, warm_X, cool_T, cool_X = split_warm_cool(experiment)
    windows = np.linspace(min_temp_window, max_temp_window, steps)
    fig, axs = plt.subplots(ncols=2, nrows=1, figsize=(12, 6))

    # Normalize the colormap
    norm = colors.Normalize(vmin=min_temp_window, vmax=max_temp_window)

    for window in windows:
        _, warm_avg_chis, _, warm_chi_vars = X_T_running_average(warm_T, warm_X, window)
        warm_avg_rms, warm_avg_variance = calculate_avg_variance_and_rms(warm_X, warm_avg_chis, warm_chi_vars)
        _, cool_avg_chis, _, cool_chi_vars = X_T_running_average(cool_T, cool_X, window)  
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

def plot_MPMS_AC_X_T(experiment, frequency=None, phase='in', figsize=(6,6)):
    """
    This function plots the AC susceptibility data from the MPMS-X for a given experiment
    
    Parameters
    ----------
    experiment : pandas DataFrame
        The experiment table from the MagIC contribution
    frequency : float
        The frequency of the AC measurement in Hz
    phase : str
        The phase of the AC measurement ('in' or 'out' or 'both')
    """
    assert phase in ['in', 'out', 'both'], 'phase should be either "in" or "out" or "both"'
    assert frequency is None or frequency in experiment['frequency'].unique(), 'frequency should be one of the available frequencies'

    if frequency is None:
        # that means we will plot all frequencies
        meas_freqs = experiment['meas_freq'].unique()
    else:
        meas_freqs = [frequency]

    if phase != 'both':
        
        fig, ax = plt.subplots(figsize=figsize)
        for meas_freq in meas_freqs:
            data = experiment[(experiment['meas_freq']==meas_freq)]
            # plot the data
            if phase == 'in':
                ax.plot(data['meas_temp'], data['susc_chi_mass'], 'o-', label=f'{meas_freq} Hz')
            else:
                ax.plot(data['meas_temp'], data['susc_chi_qdr_mass'], 'o-', label=f'{meas_freq} Hz')

        ax.set_xlabel('Temperature (K)', fontsize=16)
        ax.set_ylabel('$m^3/kg$', fontsize=16)
        ax.set_title('AC Susceptibility '+phase+' phase', fontsize=16)
        ax.legend()
        return fig, ax
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        for meas_freq in meas_freqs:
            data = experiment[(experiment['meas_freq']==meas_freq)]
            # plot the data
            ax1.plot(data['meas_temp'], data['susc_chi_mass'], 'o-', label=f'{meas_freq} Hz')
            ax2.plot(data['meas_temp'], data['susc_chi_qdr_mass'], 'o-', label=f'{meas_freq} Hz')
        ax1.set_xlabel('Temperature (K)', fontsize=16)
        ax1.set_ylabel('$m^3/kg$', fontsize=16)
        ax1.set_title('AC Susceptibility in phase', fontsize=16)
        ax1.legend()
        ax2.set_xlabel('Temperature (K)', fontsize=16)
        ax2.set_ylabel('$m^3/kg$', fontsize=16)
        ax2.set_title('AC Susceptibility out phase', fontsize=16)
        ax2.legend()
        return fig, (ax1, ax2)


# backfield data processing functions
# ------------------------------------------------------------------------------------------------------------------
def backfield_data_processing(experiment, smooth_frac=0.0, drop_first=False):
    '''
    Function to process the backfield data including shifting the magnetic 
    moment to be positive values taking the log base 10 of the magnetic 
    field values and writing these new fields into the experiment attribute 
    table

    Parameters
    ----------
    experiment : DataFrame
        DataFrame containing the backfield data
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
    assert smooth_frac >= 0 and smooth_frac <= 1, 'smooth_frac must be between 0 and 1'
    assert isinstance(drop_first, bool), 'drop_first must be a boolean'
    # check and make sure to force drop first row if the first treat field is in the wrong direction
    if experiment['treat_dc_field'].iloc[0] > 0:
        drop_first = True
    if drop_first:
        experiment = experiment.iloc[1:].reset_index(drop=1)
    
    # to plot the backfield data in the conventional way, we need to shift the magnetization to be positive
    experiment['magn_mass_shift'] = [i - experiment['magn_mass'].min() for i in experiment['magn_mass']]
    # we then calculate the log10 of the treatment fields
    experiment['log_dc_field'] = np.log10(-experiment['treat_dc_field']*1e3)
    # loess smoothing
    spl = lowess(experiment['magn_mass_shift'], experiment['log_dc_field'], frac=smooth_frac)
    experiment['smoothed_magn_mass_shift'] = spl[:, 1]
    experiment['smoothed_log_dc_field'] = spl[:, 0]
    return experiment
    
def plot_backfield_data(experiment, figsize=(5, 12)):
    """
    Plot backfield data including raw, processed, and coercivity spectrum plots.

    Parameters
    ----------
    experiment : DataFrame
        DataFrame containing the backfield data with columns 'treat_dc_field', 
        'magn_mass', 'log_dc_field', 'magn_mass_shift', 
        'smoothed_log_dc_field', and 'smoothed_magn_mass_shift'.
    figsize : tuple of int, optional
        Size of the figure to be created (default is (5, 12)).

    Returns
    -------
    The matplotlib figure and axes objects: (fig, (ax1, ax2, ax3)).
    """
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, ncols=1, figsize=figsize)

    # raw data
    ax1.scatter(experiment['treat_dc_field'], experiment['magn_mass'], c='black', marker='o', s=10, label='raw backfield data')
    ax1.plot(experiment['treat_dc_field'], experiment['magn_mass'], c='black')
    ax1.set_xlabel('treatment field (T)', fontsize=14)
    ax1.set_ylabel('magnetization (Am$^2$/kg)', fontsize=14)
    ax1.set_title('raw backfield data')
    ax1.legend()
    # processed data as curve on top of raw scattered data points in log10 space
    ax2.scatter(experiment['log_dc_field'], experiment['magn_mass_shift'], c='grey', marker='o', s=10, label='shifted raw data')
    ax2.plot(experiment['smoothed_log_dc_field'], experiment['smoothed_magn_mass_shift'], c='k', label='smoothed shifted raw data')
    ax2ticks = ax2.get_xticks()
    ax2.set_xticklabels([f'{round(10**i, 1)}' for i in ax2ticks])
    ax2.set_xlabel('treatment field (mT)', fontsize=14)
    ax2.set_ylabel('magnetization (Am$^2$/kg)', fontsize=14)
    ax2.set_title('processed backfield data')
    ax2.legend()
    # coercivity spectrum
    # first show the raw data in the derivative space
    raw_derivatives_y = -np.diff(experiment['magn_mass_shift'])/np.diff(experiment['log_dc_field'])
    # take the middle points of the logB values, and also get rid of the nan values
    raw_derivatives_x = experiment['log_dc_field'].rolling(window=2).mean().dropna()
    # derivatives of smoothed data
    smoothed_derivatives_y = -np.diff(experiment['smoothed_magn_mass_shift'])/np.diff(experiment['smoothed_log_dc_field'])
    smoothed_derivatives_x = experiment['smoothed_log_dc_field'].rolling(window=2).mean().dropna()
    ax3.scatter(raw_derivatives_x, raw_derivatives_y, c='grey', marker='o', s=10, label='raw coercivity spectrum')
    ax3.plot(smoothed_derivatives_x, smoothed_derivatives_y, c='k', label='smoothed coercivity spectrum')
    ax3ticks = ax3.get_xticks()
    ax3.set_xticklabels([f'{round(10**i, 1)}' for i in ax3ticks])
    ax3.set_xlabel('treatment field (mT)', fontsize=14)
    ax3.set_ylabel('dM/dB', fontsize=14)
    ax3.set_title('coercivity spectrum')
    ax3.legend()
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.4, wspace=0.2)

    return fig, (ax1, ax2, ax3)

def backfield_unmixing(experiment, n_comps=1, parameters=None, iter=True, n_iter=3):
    '''
    backfield unmixing for a single experiment

    Parameters
    ----------
    experiment : DataFrame
        DataFrame containing the backfield data
        by default we unmix on the smothed data
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
    smoothed_derivatives_y = -np.diff(experiment['smoothed_magn_mass_shift'])/np.diff(experiment['smoothed_log_dc_field'])
    smoothed_derivatives_x = experiment['smoothed_log_dc_field'].rolling(window=2).mean().dropna()

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
        params[f'{prefix}amplitude'].max = np.max(smoothed_derivatives_y)
        params[f'{prefix}center'].min = experiment['smoothed_log_dc_field'].min()  # Bounds for center parameters
        params[f'{prefix}center'].max = experiment['smoothed_log_dc_field'].max()  # Bounds for center parameters
        params[f'{prefix}sigma'].min = 0
        params[f'{prefix}sigma'].max = experiment['smoothed_log_dc_field'].max()-experiment['smoothed_log_dc_field'].min()  # Bounds for sigma parameters

        if composite_model is None:
            composite_model = model
        else:
            composite_model += model

    def fitting_function(y, params, x):
        result = composite_model.fit(y, params, x=x)
        for i in range(n_comps):
            prefix = f'g{i+1}_'
            parameters.loc[i, 'amplitude'] = result.params[f'{prefix}amplitude'].value
            parameters.loc[i, 'center'] = 10**result.params[f'{prefix}center'].value # convert back to mT
            parameters.loc[i, 'sigma'] = 10**result.params[f'{prefix}sigma'].value # convert back to mT
            parameters.loc[i, 'gamma'] = result.params[f'{prefix}gamma'].value
        return result, parameters

    result, parameters = fitting_function(smoothed_derivatives_y, params, x=smoothed_derivatives_x)

    if iter:
        for i in range(n_iter):
            result, parameters = fitting_function(smoothed_derivatives_y, result.params, x=smoothed_derivatives_x)

    return result, parameters

def plot_backfield_unmixing_result(experiment, result, sigma=2, figsize=(8,6)):
    raw_derivatives_y = -np.diff(experiment['magn_mass_shift'])/np.diff(experiment['log_dc_field'])
    raw_derivatives_x = experiment['log_dc_field'].rolling(window=2).mean().dropna()
    smoothed_derivatives_x = experiment['smoothed_log_dc_field'].rolling(window=2).mean().dropna()

    comps = result.eval_components(x=smoothed_derivatives_x)
    dely = result.eval_uncertainty(sigma=sigma)

    fig, ax = plt.subplots(figsize=figsize)
    # first plot the scatter raw dMdB data
    ax.scatter(raw_derivatives_x, raw_derivatives_y, c='grey', marker='o', s=10, label='raw coercivity spectrum')
    # plot the total best fit
    ax.plot(raw_derivatives_x, result.best_fit, '-', color='k', alpha=0.6, label='total spectrum best fit')
    ax.fill_between(smoothed_derivatives_x,
                            result.best_fit-dely,
                            result.best_fit+dely,
                            color="#8A8A8A", 
                            label=f'total {sigma}-$\sigma$ band', alpha=0.5)
    if len(result.components) > 1:
        for i in range(len(result.components)):

            ax.plot(smoothed_derivatives_x, comps[f'g{i+1}_'], c=f'C{i}', label=f'component #{i+1}, {sigma}-$\sigma$ band')
            ax.fill_between(smoothed_derivatives_x,
                                    comps[f'g{i+1}_']-result.dely_comps[f'g{i+1}_'],
                                    comps[f'g{i+1}_']+result.dely_comps[f'g{i+1}_'],
                                    color=f'C{i}', alpha=0.5)
    xticks = ax.get_xticks()
    ax.set_xticklabels([f'{int(10**i)}' for i in xticks])
    ax.legend()
    ax.set_title('coercivity unmixing results')
    ax.set_xlabel('treatment field (mT)', fontsize=14)
    ax.set_ylabel('dM/dB', fontsize=14)
    return fig, ax



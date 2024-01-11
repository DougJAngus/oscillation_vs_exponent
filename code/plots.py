# -*- coding: utf-8 -*-
"""
Plotting functions
"""

# Imports
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import Normalize, LogNorm, CenteredNorm, TwoSlopeNorm

# set plotting parameers
mpl.rcParams['figure.facecolor'] = 'w'
mpl.rcParams['axes.facecolor'] = 'w'
mpl.rcParams['figure.titlesize'] = 18
mpl.rcParams['axes.titlesize'] = 16
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['xtick.labelsize'] = 12
mpl.rcParams['ytick.labelsize'] = 12
mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['font.size'] = 10

def plot_tfr(time, freqs, tfr, fname_out=None, title=None,
             norm_type='log', vmin=None, vmax=None, fig=None, ax=None,
             cax=None, cbar_label=None, annotate_zero=False):
    """
    Plot time-frequency representation (TFR)

    Parameters
    ----------
    time : 1D array
        Time vector.
    freqs : 1D array
        Frequency vector.
    tfr : 2D array
        Time-frequency representation of power (spectrogram).
    fname_out : str, optional
        File name to save figure. The default is None.
    title : str, optional
        Title of plot. The default is None.
    norm_type : str, optional
        Type of normalization for color scale. Options are 'linear', 'log',
        'centered', and 'two_slope'. The default is 'log'.
    vmin, vmax : float, optional
        Minimum/maximum value for color scale. The default is None, which
        sets the min/max to the min/max of the TFR.
    fig : matplotlib figure, optional
        Figure to plot on. The default is None, which creates a new figure.
    ax : matplotlib axis, optional
        Axis to plot on. The default is None, which creates a new axis.
    cax : matplotlib axis, optional
        Axis to plot colorbar on. The default is None.
    cbar_label : str, optional
        Label for colorbar. The default is None.

    Returns
    -------
    fNone.
    """

    # imports
    from matplotlib.cm import ScalarMappable

    # Define a color map and normalization of values
    if vmin is None:
        vmin = np.nanmin(tfr)
    if vmax is None:
        vmax = np.nanmax(tfr)

    if norm_type == 'linear':
        norm = Normalize(vmin=vmin, vmax=vmax)
        cmap = 'hot'
    elif norm_type == 'log':
        norm = LogNorm(vmin=vmin, vmax=vmax)
        cmap = 'hot'
    elif norm_type == 'centered':
        norm = CenteredNorm(vcenter=0)
        cmap = 'coolwarm'
    elif norm_type == 'two_slope':
        norm = TwoSlopeNorm(vcenter=0, vmin=vmin, vmax=vmax)
        cmap = 'coolwarm'
    else:
        print("norm_type must be 'linear', 'log', 'centered', or 'two_slope'")
    
    # create figure
    if ax is None:
        fig, ax = plt.subplots(constrained_layout=True)

    # plot tfr
    ax.pcolor(time, freqs, tfr, cmap=cmap, norm=norm)

    # set labels and scale
    ax.set(yscale='log')
    ax.set_yticks([10, 100])
    ax.set_yticklabels(['10','100'])

    # set title
    if not title is None:
        ax.set_title(title)

    # label axes
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Frequency (Hz)')

    # add colorbar
    if cax is None:
        cbar = fig.colorbar(ScalarMappable(cmap=cmap, norm=norm), ax=ax)
    else:
        cbar = fig.colorbar(ScalarMappable(cmap=cmap, norm=norm), cax=cax)
    if not cbar_label is None:
        cbar.set_label(cbar_label)

    # annotate zero
    if annotate_zero:
        ax.axvline(0, color='k', linestyle='--', linewidth=2)

    # add grid
    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.8)

    # save fig
    if not fname_out is None:
        plt.savefig(fname_out)


def plot_data_spatial(brain_mesh, elec_pos, value=None, 
                       value_label='', title=None,
                       x_offset=None, y_offset=None, z_offset=None,
                       cpos=None, fname_out=None, off_screen=False,
                       elec_size=8, elec_color='r', cmap=None,
                       brain_color='w', brain_opacity=1, 
                       backgrouond_color='k', backend='static',
                       return_plotter=False, divide_hemispheres=False):
    """
    Plot data at electrode locations on brain surface. If value is not None, electrodes 
    are plotted as spheres with color determined by 'elec_color.'

    Parameters
    ----------
    brain_mesh : pyvista object
        Brain mesh.
    elec_pos : numpy array
        Electrode positions.
    value : numpy array, optional
        Values to plot at electrodes. The default is None.
    value_label : str, optional
        Label for colorbar. The default is ''.
    title : str, optional
        Title for plot. The default is None.
    x_offset, y_offset, z_offset : float, optional
        Offset for electrode positions to avoid overlap with brain surface. 
        The default is None.
    cpos : list, optional
        Camera position (Pyvista). The default is None.
    fname_out : str, optional
        File name to save figure. The default is None.
    off_screen : bool, optional
        Whether to plot off screen. The default is False.
    elec_size and elec_color : int, optional
        Electrode size and color for plotting. The default is 8 and 'r'.
    cmap : str, optional
        Colormap for electrodes plotted. The default is None.
    brain_color and brain_opacity: str, optional
        Brain color and opacity for plotting. The default is 'w' and 1.
    backgrouond_color : str, optional
        Background color of plot. The default is 'k'.
    backend : str, optional
        Jupyter backend for plotting. The default is 'static'.
    return_plotter : bool, optional
        Whether to return the plotter object. The default is False.
    divide_hemispheres : bool, optional
        Whether to divide hemispheres with a plane. The default is False.
    """
    # imports
    import pyvista as pv
    
    # shift electrode positions to avoid overlap with brain surface
    if not x_offset is None:
        elec_pos[:, 0] = elec_pos[:, 0] + x_offset
    if not y_offset is None:
        elec_pos[:, 1] = elec_pos[:, 1] + y_offset
    if not z_offset is None:
        elec_pos[:, 2] = elec_pos[:, 2] + z_offset
    
    # create figure and add brain mesh
    plotter = pv.Plotter(off_screen=off_screen)
    plotter.set_background(backgrouond_color)
    plotter.add_mesh(brain_mesh, color=brain_color, opacity=brain_opacity)
    
    # plot electrodes
    if value is None:
        plotter.add_mesh(pv.PolyData(elec_pos), point_size=elec_size, color=elec_color, \
                        render_points_as_spheres=True)
    else:
        scalar_bar_args = {'title' : value_label, 'title_font_size' : 26}
        if cmap is None:
            plotter.add_mesh(pv.PolyData(elec_pos), point_size=elec_size, scalars=value, \
                            render_points_as_spheres=True, scalar_bar_args=scalar_bar_args)
        else:
            plotter.add_mesh(pv.PolyData(elec_pos), point_size=elec_size, scalars=value, \
                            cmap=cmap, render_points_as_spheres=True, scalar_bar_args=scalar_bar_args)  
        
    # add plane to divide hemisphers
    if divide_hemispheres:
        l = 400
        verts = np.array([[0,l,l], [0,l,-l], [0,-l,-l], [0,-l,l]])
        faces = np.array([4,0,1,2,3])
        divider = pv.PolyData(verts, faces)
        plotter.add_mesh(divider, color=backgrouond_color)

    # set camera position
    if cpos is not None:
        plotter.camera_position = cpos

    # add title
    if title is not None:
        plotter.add_text(title, position='upper_left', font_size=20)

    # save figure
    if fname_out is not None:
        plotter.screenshot(fname_out)

    # plot
    if not off_screen:
        plotter.show(jupyter_backend=backend)

    # return plotter
    if return_plotter:
        return plotter.screenshot()
    else:
        plotter.close()

        
def plot_binary_spatial(brain_mesh, elec_pos, binary, title=None,
                        x_offset=None, y_offset=None, z_offset=None,
                        cpos=None, fname_out=None, off_screen=False,
                        elec_size=8, elec_colors=['r','grey'], 
                        brain_color='w', brain_opacity=1, 
                        backgrouond_color='k', backend='static',
                        divide_hemispheres=False):
    """
    Plot binary data at electrode locations on brain surface. 

    Parameters
    ----------
    brain_mesh : pyvista object
        Brain mesh.
    elec_pos : numpy array
        Electrode positions.
    binary : numpy array of bool
        Binary values to plot at electrodes. (True = elec_color[0], False = elec_color[1])
    title : str, optional
        Title for plot. The default is None.
    x_offset, y_offset, z_offset : float, optional
        Offset for electrode positions to avoid overlap with brain surface. 
        The default is None.
    cpos : list, optional
        Camera position (Pyvista). The default is None.
    fname_out : str, optional
        File name to save figure. The default is None.
    off_screen : bool, optional
        Whether to plot off screen. The default is False.
    elec_size and elec_color : int, optional
        Electrode size and color for plotting. The default is 8 and 'r'.
    cmap : str, optional
        Colormap for electrodes plotted. The default is None.
    brain_color and brain_opacity: str, optional
        Brain color and opacity for plotting. The default is 'w' and 1.
    backgrouond_color : str, optional
        Background color of plot. The default is 'k'.
    backend : str, optional
        Jupyter backend for plotting. The default is 'static'.
    divide_hemispheres : bool, optional
        Whether to divide hemispheres with a plane. The default is False.
    """
    # imports
    import pyvista as pv
    
    # shift electrode positions to avoid overlap with brain surface
    if not x_offset is None:
        elec_pos[:, 0] = elec_pos[:, 0] + x_offset
    if not y_offset is None:
        elec_pos[:, 1] = elec_pos[:, 1] + y_offset
    if not z_offset is None:
        elec_pos[:, 2] = elec_pos[:, 2] + z_offset
    
    # create figure and add brain mesh
    plotter = pv.Plotter(off_screen=off_screen)
    plotter.set_background(backgrouond_color)
    plotter.add_mesh(brain_mesh, color=brain_color, opacity=brain_opacity)
    
    # plot electrodes - color according to significance value
    chans_sig = pv.PolyData(elec_pos[binary])
    plotter.add_mesh(chans_sig, point_size=elec_size, color=elec_colors[0], \
                     render_points_as_spheres=True)
    chans_ns = pv.PolyData(elec_pos[~binary])
    plotter.add_mesh(chans_ns, point_size=elec_size, color=elec_colors[1], \
                    render_points_as_spheres=True)
    
    # add plane to divide hemisphers
    if divide_hemispheres:
        l = 400
        verts = np.array([[0,l,l], [0,l,-l], [0,-l,-l], [0,-l,l]])
        faces = np.array([4,0,1,2,3])
        divider = pv.PolyData(verts, faces)
        plotter.add_mesh(divider, color=backgrouond_color)

    # set camera position
    if cpos is not None:
        plotter.camera_position = cpos

    # add title
    if title is not None:
        plotter.add_text(title, position='upper_left', font_size=20)

    # save figure
    if fname_out is not None:
        plotter.screenshot(fname_out)

    # plot
    if not off_screen:
        plotter.show(jupyter_backend=backend)
    else:
        plotter.close()

def find_cpos_interactive():
    """
    Plot brain mesh as interactive pyvista plot, then return and print 
    final camera position.
    NOTE: must be in base director of Fellner data repository.

    Returns
    -------
    cpos : 1x3 array
        final campera position of interactive pyvista plot

    """
    # imports
    import pyvista as pv
    from scipy.io import loadmat

    # Load brain mesh data
    fname_in = r"C:\Users\micha\datasets\SpectraltiltvsOscillations\Scripts\additional scripts\surface_pial_both.mat"
    data_mesh = loadmat(fname_in, variable_names=('mesh'))
    pos = data_mesh['mesh']['pos'][0][0]
    tri = data_mesh['mesh']['tri'][0][0] - 1 # matlab index begins at 1
    
    # create pyvista object for hemisphere
    faces = np.hstack((3*np.ones((tri.shape[0],1)),tri))
    brain = pv.PolyData(pos,faces.astype(int))
    
    # create figure and add brain mesh
    plotter = pv.Plotter()
    plotter.add_mesh(brain)
    
    # show
    cpos = plotter.show(interactive=True)
    print(plotter.camera_position)
    plotter.close()
    
    return cpos


def plot_ap_params(params, time):
    """
    Plot time-series of aperiodic parameters.
    
    Parameters
    ----------
    params : FOOOFGroup object
        FOOOFGroup object containing aperiodic parameters.
    time : numpy array
        Time points corresponding to each aperiodic parameter.

    Returns
    -------
    None.
    """
    
    # imports
    from specparam_utils import extract_ap_params
    from neurodsp.plts import plot_time_series
    
    # get ap params
    offset, knee, exponent = extract_ap_params(params)
    
    # plot each ap param
    for var, variable in zip([offset, knee, exponent], 
                             ['offset', 'knee', 'exponent']):
        
        # skip knee if not fit
        if np.isnan(var).all(): continue
        
        # plot
        plot_time_series(time, var, title=variable)


def plot_spectra_2conditions(psd_pre, psd_post, freq, ax=None, shade_sem=True,
                             color=['grey','k'], labels=['baseline','encoding'],
                             y_units='\u03BCV\u00b2/Hz', title=None, fname=None):
    
    """
    Plot mean spectra for two conditions, with optional shading of SEM.

    Parameters
    ----------
    psd_pre : 2d array
        PSD values for baseline condition.
    psd_post : 2d array
        PSD values for encoding condition.
    freq : 1d array
        Frequency values corresponding to PSD values.
    ax : matplotlib axis, optional
        Axis to plot on. The default is None.
    shade_sem : bool, optional
        Whether to shade SEM. The default is True.
    color : list, optional
        Colors for each condition. The default is ['grey','k'].
    labels : list, optional
        Labels for each condition. The default is ['baseline','encoding'].
    y_units : str, optional
        Units for y-axis. The default is '\u03BCV\u00b2/Hz' (microvolts).
    title : str, optional
        Title for plot. The default is None.
    fname : str, optional
        File name to save figure. The default is None.

    Returns
    -------
    None.
    """

    # check axis
    if ax is None:
        fig, ax = plt.subplots(1,1, figsize=[6,4])

    # check psds are 2d
    if not (psd_pre.ndim == 2 and psd_post.ndim == 2):
        raise ValueError('PSDs must be 2d arrays.')
    
    # remove rows containing all nans
    psd_pre = psd_pre[~np.isnan(psd_pre).all(axis=1)]
    psd_post = psd_post[~np.isnan(psd_post).all(axis=1)]

    # plot mean spectra for each condition
    ax.loglog(freq, np.mean(psd_pre, axis=0), color=color[0], label=labels[0])
    ax.loglog(freq, np.mean(psd_post, axis=0), color=color[1], label=labels[1])
    
    # shade between SEM of spectra for each condition
    if shade_sem:
        ax.fill_between(freq, np.mean(psd_pre, axis=0) - (np.std(psd_pre, axis=0)/np.sqrt(psd_pre.shape[0])),
                        np.mean(psd_pre, axis=0) + (np.std(psd_pre, axis=0)/np.sqrt(psd_pre.shape[0])), 
                        color=color[0], alpha=0.5)
        ax.fill_between(freq, np.mean(psd_post, axis=0) - (np.std(psd_post, axis=0)/np.sqrt(psd_post.shape[0])),
                        np.mean(psd_post, axis=0) + (np.std(psd_post, axis=0)/np.sqrt(psd_post.shape[0])),
                        color=color[1], alpha=0.5)

    # set axes ticks and labels
    ax.set_ylabel(f'power ({y_units})')
    ax.set_xlabel('frequency (Hz)')
    ax.set_xticks([10,100])
    ax.set_xticklabels(["10", "100"])

    # add legend
    ax.legend(labels)

    # add title
    if title is None:
        ax.set_title('Power spectra')
    else:
        ax.set_title(title)

    # add grid
    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)
    
    # return
    if fname is not None:
        fig.savefig(fname)


def plot_psd_diff(freq, psd_diff, title=None, fname_out=None,
                  plot_each=False, plot_mean=True, shade_sem=True,
                  y_units='\u03BCV\u00b2/Hz', ax=None):
    """ 
    Plot spectra (or change in spectral power) in semi-log space.
    The mean spectrum is plotted in black, and the individual spectra are plotted in grey.
    A horizontal line at power=0 is also plotted.

    Parameters
    ----------
    freq : array
        Frequency values.
    psd_diff : array
        Spectral power values (difference in log power between 2 spectra).
    title : str, optional
        Title of plot. The default is None.
    fname_out : str, optional
        Path to save figure to. If None, figure is not saved.
        The default is None.
    plot_each : bool, optional
        Whether to plot each individual spectrum. The default is False.
    plot_mean : bool, optional
        Whether to plot the mean spectrum. The default is True.
    shade_sem : bool, optional
        Whether to shade the standard error of the mean. The default is True.
    y_units : str, optional
        Units for y-axis. The default is '\u03BCV\u00b2/Hz' (microvolts).
    ax : matplotlib axis, optional
        Axis to plot on. If None, a new figure is created.

    Returns
    -------
    None.
    
    """
    # create figure
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6,4))

    # plot psd
    if plot_each:
        ax.plot(freq, psd_diff.T, color='grey')

    # plot mean
    if plot_mean:
        ax.plot(freq, np.nanmean(psd_diff, axis=0), color='k', linewidth=3,
                label="mean")

    # shade sem
    if shade_sem:
        mean = np.nanmean(psd_diff, axis=0)
        sem = np.nanstd(psd_diff, axis=0) / np.sqrt(psd_diff.shape[0])
        ax.fill_between(freq, mean - sem, mean + sem,
                        color='k', alpha=0.2, label="SEM")

    # legend
    try:
        ax.legend()
    except:
        pass

    # scale x-axis logarithmically
    ax.set(xscale="log")

    # set axes ticks and labels
    ax.set_ylabel(f'log power ({y_units})')
    ax.set_xlabel('frequency (Hz)')
    ax.set_xticks([10,100])
    ax.set_xticklabels(["10", "100"])

    # title
    if title is None:
        ax.set_title(f"Difference in power")
    else:
        ax.set_title(title)

    # annotate power=0
    ax.axhline(0, color='r', linestyle='--', linewidth=3)

    # add grid
    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)

    # save
    if not fname_out is None:
        plt.savefig(fname_out)


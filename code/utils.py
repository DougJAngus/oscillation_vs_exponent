# -*- coding: utf-8 -*-
"""
Utility functions
"""

# Imports
import numpy as np

def zscore_tfr(tfr):
    """
    Normalize time-frequency representation (TFR) by z-scoring each frequency.
    TFR should be 2D (frequency x time).

    Parameters
    ----------
    tfr : 2D array
        Time-frequency representation of power (spectrogram).

    Returns
    -------
    tfr_norm : 2D array
        Z-score normalized TFR.
    """
    
    # initialize 
    tfr_norm = np.zeros(tfr.shape)
    
    # z-score normalize 
    for i_freq in range(tfr.shape[0]):
        tfr_norm[i_freq] = (tfr[i_freq] - np.mean(tfr[i_freq])) / np.std(tfr[i_freq])
        
    return tfr_norm

def subtract_baseline(signals, time, t_baseline):
    """
    Subtract baseline from signals. Baseline is defined as the mean of the
    signal between t_baseline[0] and t_baseline[1]. Signals should be 2D
    (signals x time).

    Parameters
    ----------
    signals : 2D array
        Signals to be baseline corrected.
    time : 1D array
        Time vector.
    t_baseline : 1D array
        Time range for baseline (t_start, t_stop).

    Returns
    -------
    signals_bl : 2D array
        Baseline corrected signals.
    """
    
    # initialize
    signals_bl = np.zeros_like(signals)
    
    # subtract baseline from each signal
    for ii in range(len(signals)):
        mask_bl = ((time>t_baseline[0]) & (time<t_baseline[1]))
        bl = np.mean(signals[ii, mask_bl])
        signals_bl[ii] = signals[ii] - bl
    
    return signals_bl

def crop_tfr(tfr, time, time_range):
    """
    Crop time-frequency representation (TFR) to time_range.
    TFR can be mulitdimensional (time must be last dimension).

    Parameters
    ----------
    tfr : array
        Time-frequency representation of power (spectrogram).
    time : 1D array
        Associated time vector (length should be equal to that of
        the last dimension of tfr).
    time_range : 1D array
        Time range to crop (t_start, t_stop).

    Returns
    -------
    tfr, time : array, array
        Cropped TFR and time vector.
    """
    
    tfr = tfr[..., (time>time_range[0]) & (time<time_range[1])]
    time = time[(time>time_range[0]) & (time<time_range[1])]
    
    return tfr, time

def downsample_tfr(tfr, time, n):
    """
    Downsample time-frequency representation (TFR) to n time bins.
    TFR can be mulitdimensional (time must be last dimension)

    Parameters
    ----------
    tfr : array
        Time-frequency representation of power (spectrogram).
    time : 1D array
        Associated time vector (length should be equal to that of 
        the last dimension of tfr).
    n : int
        Desired number of time bins after downsampling.

    Returns
    ------- 
    tfr, time : array, array
        Downsampled TFR and time vector.
    """

    # determine step size for downsampling and counnt number of samples
    n_samples = len(time)
    step = int(np.floor(tfr.shape[-1]/n))

    # downsample
    tfr = tfr[..., np.arange(0, n_samples-1, step)] 
    time = time[np.arange(0, n_samples-1, step)] 
    
    return tfr, time


def hour_min_sec(duration):
    """
    Convert duration in seconds to hours, minutes, and seconds.

    Parameters
    ----------
    duration : float
        Duration in seconds.

    Returns
    -------
    hours, mins, secs : int
        Duration in hours, minutes, and seconds.
    """

    hours = int(np.floor(duration / 3600))
    mins = int(np.floor(duration%3600 / 60))
    secs = int(duration % 60)
    
    return hours, mins, secs


def knee_freq(knee, exponent):
    """
    Convert specparam knee parameter to Hz.

    Parameters
    ----------
    knee, exponent : 1D array
        Knee and exponent parameters from specparam.

    Returns
    -------
    knee_hz : 1D array
        Knee in Hz.
    """
    knee_hz = np.zeros_like(knee)
    for ii in range(len(knee)):
        knee_hz[ii] = knee[ii]**(1/exponent[ii])
    
    return knee_hz


def extract_ap_params(params):
    """
    Extract aperiodic parameters from FOOOFGroup object.

    Parameters
    ----------
    params : FOOOFGroup object
        FOOOFGroup object containing aperiodic parameters.

    Returns
    -------
    offset, knee, exponent : 1D array
        Offset, knee, and exponent parameters.
    
    """
    # get aperiodic parameter time-series
    offset = params.get_params('aperiodic', 'offset')
    exponent = params.get_params('aperiodic', 'exponent')
    
    # check if knee data exists
    try:
        # convert k to Hz
        k = params.get_params('aperiodic', 'knee')
        knee = knee_freq(k, exponent)
    except:
        knee = [np.nan] * len(offset)
    
    return offset, knee, exponent


def load_ap_params(fname):
    """
    Load specparam results from file and extract aperiodic parameters.

    Parameters
    ----------
    fname : str
        Filename to load.

    Returns
    -------
    offset, knee, exponent : 1D array
        Offset, knee, and exponent parameters.
    """

    # imports
    from fooof import FOOOFGroup

    # import specparam results
    params = FOOOFGroup()
    params.load(fname)
    
    return extract_ap_params(params)

def generate_ap_spectra(params):
    """
    Simulate aperiodic power spectra from FOOOFGroup object.

    Parameters
    ----------
    params : FOOOFGroup object
        FOOOFGroup object containing aperiodic parameters.

    Returns
    -------
    spectra: array
        Aperiodic power spectra.

    """
    # imports
    from fooof.sim import gen_power_spectrum

    # init
    spectra = np.zeros([len(params), len(params.freqs)])
    
    # simulate aperiodic spectra for each 
    for ii in range(len(params)):
        _, spectra[ii] = gen_power_spectrum([params.freqs[0], params.freqs[-1]],
                                              params[ii].aperiodic_params, [], 
                                              freq_res=params.freq_res, nlv=0)
 

    return spectra
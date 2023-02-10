# -*- coding: utf-8 -*-
"""
Utility functions
"""

# Imports
import numpy as np

def zscore_tfr(tfr):
    """
    Normalize time-frequency representation (TFR) by z-scoring each frequency
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
    signal between t_baseline[0] and t_baseline[1]. 

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
    
    signals_bl = np.zeros_like(signals)
    
    for ii in range(len(signals)):
        mask_bl = ((time>t_baseline[0]) & (time<t_baseline[1]))
        bl = np.mean(signals[ii, mask_bl])
        signals_bl[ii] = signals[ii] - bl
    
    return signals_bl

def crop_tfr(tfr, time, time_range):
    """
    Crop time-frequency representation (TFR) to time_range
    """
    
    tfr = tfr[:, (time>time_range[0]) & (time<time_range[1])]
    time = time[(time>time_range[0]) & (time<time_range[1])]
    
    return tfr, time

def downsample_tfr(tfr, time, n):
    """
    Downsample time-frequency representation (TFR) to n time bins.
    Can be use on 2D or 3D TFRs (time must be last dimension)

    Parameters
    ----------
    tfr : 2D or 3D array
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
    
    n_samples = len(time)
    step = int(np.floor(tfr.shape[-1]/n))
    tfr = tfr[..., np.arange(0, n_samples-1, step)] 
    time = time[np.arange(0, n_samples-1, step)] 
    
    return tfr, time



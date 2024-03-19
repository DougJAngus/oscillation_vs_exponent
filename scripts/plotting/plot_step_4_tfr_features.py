"""

"""

# Imports - standard
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from specparam import SpectralGroupModel
from scipy import stats

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from info import MATERIALS
from utils import get_start_time, print_time_elapsed
from tfr_utils import trim_tfr, subtract_baseline
from plots import plot_evoked_tfr
from settings import BANDS, AP_MODE, FREQ_RANGE
from specparam_utils import compute_band_power, compute_adjusted_band_power

# settings - example data to plot
PATIENT = 'pat11'
MATERIAL = 'words'
CHANNEL = 34
X_LIMITS = [-0.25, 1.0]
Y_LIMITS = [-0.9, 0.7]

def main():

    # display progress
    t_start = get_start_time()

    # identify / create directories
    dir_output = f"{PROJECT_PATH}/figures/main_figures"
    if not os.path.exists(dir_output): 
        os.makedirs(f"{dir_output}")

    # create figure
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)

    # Plot single-electrode TFR ================================================
    fname = f'{PATIENT}_{MATERIAL}_hit_chan{CHANNEL}_tfr.npz'
    data_in = np.load(f"{PROJECT_PATH}/data/ieeg_tfr/{fname}")
    tfr_mean = np.nanmedian(np.squeeze(data_in['tfr']), axis=0) # average over trials
    tfr, freq, time = trim_tfr(tfr_mean, data_in['freq'], data_in['time'], 
                                freq_range=FREQ_RANGE, time_range=X_LIMITS)
    plot_evoked_tfr(tfr, freq, time, fig=fig, ax=axes[0,0], annotate_zero=True, 
                    cbar_label='power (z-score)', title='Single electrode')
    
    # Plot single-electrode time-series ========================================
    # load SpecParam results
    fname = f'{PATIENT}_{MATERIAL}_hit_chan{CHANNEL}_tfr_param_knee'
    sm = SpectralGroupModel()
    sm.load(f"{PROJECT_PATH}/data/ieeg_tfr_param/{fname}")
    exponent = sm.get_params('aperiodic','exponent')

    # load spectral results and compute band power
    fname = f'{PATIENT}_{MATERIAL}_hit_chan{CHANNEL}_tfr.npz'
    data_in = np.load(f"{PROJECT_PATH}/data/ieeg_tfr/{fname}")
    tfr = np.nanmean(data_in['tfr'], axis=0)
    time = data_in['time']
    power = dict()
    power_adj = dict()
    for band, f_range in BANDS.items():
        power[band] = compute_band_power(data_in['freq'], tfr.T, f_range, 
                                         method='mean', log_power=True)
        power_adj[band] = compute_adjusted_band_power(data_in['freq'], tfr.T, 
                                                      sm, f_range, 
                                                      method='mean', 
                                                      log_power=True)
        
    # plot exponent
    exponent = np.squeeze(subtract_baseline(exponent[np.newaxis,:], time, 
                                            t_baseline=[X_LIMITS[0], 0]))
    axes[0,3].plot(time, exponent)
    axes[0,3].set_title('Aperiodic exponent')
    axes[0,3].set(xlabel='time (s)', ylabel='exponent')

    # plot power
    for pow, ax in zip([power, power_adj], [axes[0,1], axes[0,2]]):
        for band in BANDS.keys():
            ts = np.squeeze(subtract_baseline(pow[band][np.newaxis, :], time,
                                                t_baseline=[X_LIMITS[0], 0]))
            ax.plot(time, ts, label=band)
        ax.legend()
        ax.set(xlabel='time (s)', ylabel='power (a.u.)')

    # # Plot group TFR ===========================================================
    # load stats
    fname = f"{PROJECT_PATH}/data/results/ieeg_modulated_channels.csv"
    df_stats = pd.read_csv(fname, index_col=0)
    df_stats = df_stats.loc[df_stats['sig_all']].reset_index(drop=True)

    # load TFR for active channels 
    tfr_list = []
    for _, row in df_stats.iterrows():
        for material in MATERIALS:
            fname = f"{row['patient']}_{material}_hit_chan{row['chan_idx']}_tfr.npz"
            data_in = np.load(f"{PROJECT_PATH}/data/ieeg_tfr/{fname}")
            tfr_list.append(np.nanmedian(np.squeeze(data_in['tfr']), axis=0))
    tfr = np.nanmean(np.array(tfr_list), axis=0) # average over channels and materials

    # plot
    tfr, freq, time = trim_tfr(tfr, data_in['freq'], data_in['time'], 
                                freq_range=FREQ_RANGE, time_range=X_LIMITS)
    plot_evoked_tfr(tfr, freq, time, fig=fig, ax=axes[1,0], annotate_zero=True, 
                    cbar_label='power (z-score)', title='Group average')

    # Plot group time-series ===================================================
    
    # initialize lists
    exp_list = []
    power = dict()
    power_adj = dict()
    for band in BANDS.keys():
        power[band] = []
        power_adj[band] = []

    # aggregate data for all active channels
    for _, row in df_stats.iterrows():
        for material in MATERIALS:
            # load exponent
            fname = f"{row['patient']}_{material}_hit_chan{row['chan_idx']}_tfr_param_{AP_MODE}"
            sm = SpectralGroupModel()
            sm.load(f"{PROJECT_PATH}/data/ieeg_tfr_param/{fname}")
            exp_list.append(sm.get_params('aperiodic','exponent'))
            
            # load tfr and compute band power
            fname = f"{row['patient']}_{material}_hit_chan{row['chan_idx']}_tfr.npz"
            data_in = np.load(f"{PROJECT_PATH}/data/ieeg_tfr/{fname}")
            tfr = np.nanmedian(np.squeeze(data_in['tfr']), axis=0)
            
            for band, f_range in BANDS.items():
                temp = compute_band_power(data_in['freq'], tfr.T, f_range, 
                                          method='mean', log_power=True)
                power[band].append(temp)
                temp = compute_adjusted_band_power(data_in['freq'], tfr.T, sm, 
                                                   f_range, method='mean', 
                                                   log_power=True)
                power_adj[band].append(temp)

    # convert to arrays
    exponent = np.array(exp_list)
    for band in BANDS.keys():
        power[band] = np.array(power[band])
        power_adj[band] = np.array(power_adj[band])
    
    # subtract baseline
    time = data_in['time']
    exponent = subtract_baseline(exponent, time, t_baseline=[X_LIMITS[0], 0])
    for band in BANDS.keys():
        power[band] = subtract_baseline(power[band], time, 
                                        t_baseline=[X_LIMITS[0], 0])
        power_adj[band] = subtract_baseline(power_adj[band], time, 
                                            t_baseline=[X_LIMITS[0], 0])

    # plot exponent
    ci= compute_ci(exponent)
    axes[1,3].plot(time, np.nanmean(exponent, axis=0), label='exponent')
    axes[1,3].fill_between(time, ci[0], ci[1], alpha=0.2)
    axes[1,3].set_title('Aperiodic exponent')
    axes[1,3].set(xlabel='time (s)', ylabel='exponent')

    # plot power
    for pow, ax in zip([power, power_adj], [axes[1,1], axes[1,2]]):
        for band in BANDS.keys():
            ci = compute_ci(pow[band])
            ts = np.nanmean(pow[band], axis=0)
            ax.plot(time, ts, label=band)
            ax.fill_between(time, ci[0], ci[1], alpha=0.2)
        ax.legend()
        ax.set(xlabel='time (s)', ylabel='power (a.u.)')      

    # label and adjust plots ===================================================
    for row in [0, 1]:
        axes[row, 1].set_title('Total power')
        axes[row, 2].set_title('Adjusted power')
        for ax in axes[row, 1:]:
            ax.set_xlim(X_LIMITS)
            ax.axhline(0, color='k', linestyle='--')
            ax.axvline(0, color='k', linestyle='--')

    # set/share y axis
    for ax in axes[:, 1:3].flatten():
        ax.set_ylim(Y_LIMITS)

    # save figure
    fig.savefig(f"{dir_output}/tfr_features.png", dpi=300)

    # display progress
    print(f"\n\nTotal analysis time:")
    print_time_elapsed(t_start)


def compute_ci(data):
    mean = np.nanmean(data, axis=0)
    sem = stats.sem(data, axis=0, nan_policy='omit')
    ci = np.array([mean - sem, mean + sem])

    return ci


if __name__ == "__main__":
    main()

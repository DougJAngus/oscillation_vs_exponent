"""

"""

# Imports - standard
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from specparam import SpectralGroupModel
from specparam.utils import trim_spectrum

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from info import MATERIALS
from utils import get_start_time, print_time_elapsed, confidence_interval
from tfr_utils import trim_tfr, subtract_baseline
from tfr_utils import zscore_tfr as zscore
from plots import plot_evoked_tfr
from settings import BANDS, AP_MODE, FREQ_RANGE, BCOLORS
from specparam_utils import compute_band_power
from specparam_utils import _compute_adjusted_band_power as compute_adjusted_band_power

# settings - analysis (match to other analyses)
LOG_POWER = True # log-transform power
METHOD = 'mean' # method for computing band power

# settings - figure
plt.style.use('mplstyle/default.mplstyle')
FIGSIZE = (6.5, 2)
X_LIMITS = [-0.5, 1.0] # for time-series plots
Y_LIMITS = [-2.2, 2.2]


def main():

    # display progress
    t_start = get_start_time()

    # identify / create directories
    dir_output = f"{PROJECT_PATH}/figures/main_figures"
    if not os.path.exists(dir_output): 
        os.makedirs(f"{dir_output}")

    # create figure
    fig, axes = plt.subplots(1, 3, figsize=FIGSIZE, constrained_layout=True)

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
    plot_evoked_tfr(tfr, freq, time, fig=fig, ax=axes[0], annotate_zero=True, 
                    cbar_label='power (au)')

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
                                          method=METHOD, log_power=LOG_POWER)
                power[band].append(temp)
                
                freq, spectra = trim_spectrum(data_in['freq'], tfr.T, FREQ_RANGE)
                temp = compute_adjusted_band_power(freq, spectra, sm, 
                                                   f_range, method=METHOD, 
                                                   log_power=LOG_POWER)
                power_adj[band].append(temp)
    
    # z-score power and subtract baseline
    time = data_in['time']
    for band in BANDS.keys():
        # convert to arrays
        power[band] = np.array(power[band])
        power_adj[band] = np.array(power_adj[band])

        # z-score
        power[band] = zscore(power[band])
        power_adj[band] = zscore(power_adj[band])

        # subtract baseline
        power[band] = subtract_baseline(power[band], time, 
                                        t_baseline=[X_LIMITS[0], 0])
        power_adj[band] = subtract_baseline(power_adj[band], time, 
                                            t_baseline=[X_LIMITS[0], 0])

    # plot power
    for pow, ax in zip([power, power_adj], [axes[1], axes[2]]):
        for band in BANDS.keys():
            ci = confidence_interval(pow[band])
            ax.plot(time, np.nanmean(pow[band], axis=0), label=band, color=BCOLORS[band])
            ax.fill_between(time, ci[0], ci[1], alpha=0.2, color=BCOLORS[band])

    # plot exponent (after z-scoreing and subtracting baseline)
    exponent = subtract_baseline(zscore(np.array(exp_list)), time, 
                                 t_baseline=[X_LIMITS[0], 0])
    ci = confidence_interval(exponent)
    axes[2].plot(time, np.nanmean(exponent, axis=0), label='exponent', color=BCOLORS['exponent'])
    axes[2].fill_between(time, ci[0], ci[1], alpha=0.2, color=BCOLORS['exponent'])

    # label and adjust plots ===================================================
    # set title
    # axes[1].set_title('Total power')
    # axes[2].set_title('Adjusted power')

    # set x and y labels
    # for ax in axes[1:3]:
    axes[1].set_ylabel('total power (au)')
    axes[2].set_ylabel('adjusted power (au)')
    for ax in axes:
        ax.set_xlabel('time (s)')
        
    # set x labels and limits
    for ax in axes[1:3]:
        ax.axhline(0, color='k', linestyle='--')
        ax.axvline(0, color='k', linestyle='--')
        ax.set_xlim(X_LIMITS)

    # adjust y limits
    for ax in axes[1:3]:
        ax.set_ylim(Y_LIMITS)

    # add legend
    for ax in axes[1:3]:
        ax.legend(loc='upper left', facecolor='white')
    # axes[1].legend(loc='lower left', facecolor='white')
    # axes[2].legend(loc='upper left', facecolor='white')

    # save figure
    fig.savefig(f"{dir_output}/tfr_features_group.png")

    # display progress
    print(f"\n\nTotal analysis time:")
    print_time_elapsed(t_start)


if __name__ == "__main__":
    main()
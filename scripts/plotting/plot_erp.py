"""
This script plots the ERP for each channel in the dataset. Additionally, the
ERP amplitude is computed as the ratio of the maximum ERP amplitude after the
stimulus onset to the maximum ERP amplitude before the stimulus onset. The
results are saved in a dataframe and the ERP plots are saved as PNG files.


"""

# Imports - general
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mne import read_epochs
from time import time as timer

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from utils import hour_min_sec
from tfr_utils import crop_tfr
from erp_utils import compute_erp, plot_erp

# settings 
T_BASELINE = [-0.5, 0.] # baseline time window for ERP computation
T_TRIM = [-0.5, 2.] # time window to trim signal    
plt.style.use('mplstyle/default.mplstyle')

def main():
    # display progress
    t_start = timer()

    # identify / create directories
    dir_input = f"{PROJECT_PATH}/data/ieeg_epochs"
    dir_output = f"{PROJECT_PATH}/data/results"
    dir_fig = f"{PROJECT_PATH}/figures/erp"
    if not os.path.exists(dir_output): os.makedirs(dir_output)
    if not os.path.exists(dir_fig): os.makedirs(dir_fig)
    
    # init
    df_erp = pd.DataFrame(columns=['patient', 'chan_idx', 'material', 'memory', 
                                   'erp_max_pre', 'erp_max_post', 'erp_amp'])

    # for each fif file
    files = os.listdir(dir_input)
    for ii, fname in enumerate(files):

        # display progress
        t_start_f = timer()
        print(f"\nAnalyzing file {ii+1}/{len(files)}")
        print(f"\tfilename: \t{fname}")

        # load eeg data
        epochs = read_epochs(f"{dir_input}/{fname}", verbose=False)
        signals = epochs.get_data()
        time = epochs.times
        print(f"\tchannels: \t{len(epochs.info['ch_names'])}")
    
        # compute erp
        erps = compute_erp(signals, time, T_BASELINE)

        # trim signal
        erps, time = crop_tfr(erps, time, T_TRIM)

        # compute ERP amplitude and add to df
        erps_abs = np.abs(erps)
        erp_max_pre = np.nanmax(erps_abs[:, time<0], axis=1)
        erp_max_post = np.nanmax(erps_abs[:, time>0], axis=1)
        erp_amp = erp_max_post / erp_max_pre
        fparts = fname.split('_')
        df_i = pd.DataFrame({'patient' : fparts[0],
                            'chan_idx' : np.arange(erps.shape[0]),
                            'material' : fparts[1],
                            'memory' : fparts[2],
                            'erp_max_pre' : erp_max_pre,
                            'erp_max_post' : erp_max_post,
                            'erp_amp' : erp_amp})
        df_erp = pd.concat([df_erp, df_i], axis=0)  

        # plot erp for each channel
        for channel in range(erps.shape[0]):
            # plot
            plot_erp(erps[channel], time)

            # set title
            ax = plt.gca()
            fname_fig = fname.replace('_epo.fif', f'_chan{channel}')
            ax.set_title(fname_fig)

            # save figure
            fig = plt.gcf()
            fig.set_size_inches(6,4)
            fig.savefig(f"{dir_fig}/{fname_fig}.png")
            plt.close('all')

        # display progress
        hour, min, sec = hour_min_sec(timer() - t_start_f)
        print(f"\tanalysis time: \t{hour} hour, {min} min, and {sec :0.1f} s")

    # save df
    df_erp.to_csv(f"{dir_output}/df_erp.csv", index=False)

    # display progress
    hour, min, sec = hour_min_sec(timer() - t_start)
    print(f"\n\nTotal analysis time: {hour} hour, {min} min, and {sec :0.1f} s")
    

if __name__ == "__main__":
    main()
    
    
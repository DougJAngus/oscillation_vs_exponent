"""
Identify channels with significant modulation of alpha/beta bandpower

"""

# Set path
PROJECT_PATH = 'C:/Users/micha/projects/oscillation_vs_exponent/'

# ignore mean of empty slice warnings
import warnings
warnings.filterwarnings("ignore")

# Imports - general
import os
import numpy as np
import pandas as pd
from time import time as timer
from time import ctime as time_now
from fooof.utils import trim_spectrum

# Imports - custom
from stats import run_resampling_analysis
from utils import hour_min_sec

# dataset details
FS = 512 # meg sampling frequency
TMIN = -1.5 # epoch start time
PATIENTS = ['pat02','pat04','pat05','pat08','pat10','pat11',
         'pat15','pat16','pat17','pat19','pat20','pat21','pat22']

# anlysis parameters
ALPHA_BAND = [8, 20] # alpha/beta frequnecy range
N_ITER = 10000 # random permutation iterations/shuffles
ALPHA = 0.05 # significance level

def main():
   # time it

    t_start = timer()

    # identify / create directories
    dir_input = f"{PROJECT_PATH}/data/ieeg_psd/"
    files = os.listdir(dir_input)
    dir_output = f"{PROJECT_PATH}/data/results"
    if not os.path.exists(dir_output): 
        os.makedirs(f"{dir_output}")

    # loop through conditions
    dfs = []
    for material in ['words','faces']:
        for memory in ['hit','miss']:
            for patient in PATIENTS:
                # display progress
                t_start_i = timer()
                print(f"\nAnalyzing: {material} - {memory} - {patient}")
                print(f"    Current time: \t{time_now()}")
                
                # init dataframe
                columns=['patient', 'material', 'memory', 'chan_idx', 'p_val', 'sign']
                df = pd.DataFrame(columns=columns)
                
                # load pre- and post-stim psd 
                fname_in = f"{patient}_{material}_{memory}_XXXstim_psd.npz"
                data_pre = np.load(f"{dir_input}/{fname_in.replace('XXX','pre')}")
                data_post = np.load(f"{dir_input}/{fname_in.replace('XXX','post')}")

                # get number of trials and channels
                n_trials = data_pre['psd'].shape[0]
                n_chans = data_pre['psd'].shape[1]
                print(f"    file contains {n_trials} trials and {n_chans} channels...")

                # save metadata
                df['chan_idx'] = np.arange(n_chans)
                df['patient'] = patient
                df['material'] = material
                df['memory'] = memory

                # initialize arrays for alpha band power
                alpha_pre = np.zeros([n_chans, n_trials])
                alpha_post = np.zeros([n_chans, n_trials])

                # loop through channels
                for i_chan in range(n_chans):
                    # check if data is missing (contains all NaN)
                    if np.isnan(data_pre['psd'][:,i_chan]).all() or np.isnan(data_post['psd'][:,i_chan]).all():
                        # save results and continue to next channel
                        df.loc[i_chan, 'p_val'] = np.nan
                        df.loc[i_chan, 'sign'] = np.nan
                        continue

                    # trim in alpha band
                    _, alpha_band_pre = trim_spectrum(data_pre['freq'], data_pre['psd'][:,i_chan], f_range=ALPHA_BAND)
                    _, alpha_band_post = trim_spectrum(data_post['freq'], data_post['psd'][:,i_chan], f_range=ALPHA_BAND)
                    alpha_pre[i_chan] = np.nanmean(alpha_band_pre, axis=1)
                    alpha_post[i_chan] = np.nanmean(alpha_band_post, axis=1)

                    # determine whether alpha/beta bandpower was task modulation
                    p_val, sign = run_resampling_analysis(alpha_pre[i_chan],
                                                          alpha_post[i_chan], N_ITER)
                    
                    # save results
                    df.loc[i_chan, 'p_val'] = p_val
                    df.loc[i_chan, 'sign'] = sign

                # aggreate results
                dfs.append(df)

                # display progress
                hour, min, sec = hour_min_sec(timer() - t_start_i)
                print(f"    file complete in {hour} hour, {min} min, and {sec :0.1f} s")

    # concatenate results
    results = pd.concat(dfs, ignore_index=True)

    # find channels that are task modulated in both material conditions (successful trials)
    results['sig_tm'] = results['p_val'] < ALPHA # determine significance within condition
    sig = results[results['memory']=='hit'].groupby(['patient','chan_idx']).all().reset_index() # find sig chans
    results['sig'] = np.nan # init
    for ii in range(len(sig)):
        results.loc[(results['patient']==sig.loc[ii, 'patient']) & \
                    (results['chan_idx']==sig.loc[ii, 'chan_idx']), 'sig'] \
                        = sig.loc[ii, 'sig_tm'] # add results to df

    # save results
    results.to_csv(f"{dir_output}/ieeg_modulated_channels.csv")

    # display progress
    hour, min, sec = hour_min_sec(timer() - t_start)
    print(f"\n\n Total Time: \t {hour} hours, {min} minutes, {sec :0.1f} seconds")


if __name__ == "__main__":
    main()


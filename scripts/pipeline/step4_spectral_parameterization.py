"""
This script parameterizes the spectral results from 2_time_frequency_analysis.py

"""

# Imports
import os
import numpy as np
import pandas as pd
from specparam import SpectralGroupModel
from time import time as timer

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from settings import N_JOBS, SPEC_PARAM_SETTINGS, FREQ_RANGE
from utils import hour_min_sec

# Settings
RUN_TFR = False # run TFR parameterization (takes a long time)
AP_MODE = ['fixed', 'knee'] # aperiodic mode for SpecParam


def main():
    
    # parameterize PSDs
    print('\nParameterizing PSDs...')
    param_group_psd_results()

    # parameterize TFRs
    if RUN_TFR:
        print('\nParameterizing TFRs...')
        parameterize_tfr()

def param_group_psd_results():
    # identify / create directories
    dir_input = f"{PROJECT_PATH}/data/ieeg_spectral_results"
    dir_output = f"{PROJECT_PATH}/data/ieeg_psd_param"
    if not os.path.exists(dir_output): 
        os.makedirs(f"{dir_output}/reports")
    
    # display progress
    t_start = timer()
    
    # loop through conditions
    files = [f for f in os.listdir(dir_input) if f.startswith('psd') & (not 'epoch' in f)]
    for i_file, fname in enumerate(files):
        # display progress
        t_start_c = timer()
        print(f"\tAnalyzing: {fname} ({i_file+1}/{len(files)})")

        # load results for condition
        data_in =  np.load(f"{dir_input}/{fname}")
        spectra = data_in['spectra']
        freq = data_in['freq']
        
        # parameterize (fit both with and without knee parametere)
        for ap_mode in AP_MODE:
            fg = SpectralGroupModel(**SPEC_PARAM_SETTINGS, aperiodic_mode=ap_mode, verbose=False)
            fg.set_check_modes(check_freqs=False, check_data=False)
            fg.fit(freq, spectra, n_jobs=N_JOBS, freq_range=FREQ_RANGE)
            
            # save results 
            fname_out = fname.replace('.npz', f'_params_{ap_mode}')
            fg.save(f"{dir_output}/{fname_out}", save_results=True, 
                    save_settings=True, save_data=True)
            fg.save_report(f"{dir_output}/reports/{fname_out}")

        # display progress
        hour, min, sec = hour_min_sec(timer() - t_start_c)
        print(f"\t\tCondition completed in {hour} hour, {min} min, and {sec:0.1f} s")

    # display progress
    hour, min, sec = hour_min_sec(timer() - t_start)
    print(f"Total PSD analysis time: {hour} hour, {min} min, and {sec:0.1f} s")
 

def parameterize_tfr():
    # time it
    t_start = timer()

    # identify / create directories
    dir_input = f"{PROJECT_PATH}/data/ieeg_tfr"
    dir_output = f"{PROJECT_PATH}/data/ieeg_tfr_param"
    if not os.path.exists(f"{dir_output}/reports"): 
        os.makedirs(f"{dir_output}/reports")

    # load alpha/beta bandpower modulation results (resampling ananlysis)
    results = load_stats()
    df = results.loc[results['sig_either_both']].reset_index(drop=True)
    
    # loop through significant channels
    for i_chan, row in df.iterrows():
        # display progress
        print(f"    Analyzing file {i_chan}/{len(df)}") 
        t_start_c = timer()

        # loop through materials and conditions
        for material in ['words', 'faces']:
            for memory in ['hit', 'miss']:

                # check if output file already exists
                fname = f"{row['patient']}_{material}_{memory}_chan{row['chan_idx']}_tfr.npz"
                temp = f"{dir_output}/{fname.replace('.npz','_param_knee.json')}"
                if os.path.exists(temp):
                    continue

                # load tfr
                data_in = np.load(f"{dir_input}/{fname}")
                tfr_in = data_in['tfr']
                freq = data_in['freq']
                
                # average over trials
                tfr = np.squeeze(np.nanmean(tfr_in, axis=0))
                
                # parameterize
                for ap_mode in AP_MODE:
                    fg = SpectralGroupModel(**SPEC_PARAM_SETTINGS, 
                                            aperiodic_mode=ap_mode, verbose=False)
                    fg.set_check_modes(check_freqs=False, check_data=False)
                    fg.fit(freq, tfr.T, n_jobs=N_JOBS, freq_range=FREQ_RANGE)
                    
                    # save results and report
                    fname_out = fname.replace('.npz','_param_%s' %ap_mode)
                    fg.save(f"{dir_output}/{fname_out}", save_results=True, 
                            save_settings=True)
                    fg.save_report(f"{dir_output}/reports/{fname_out}")

        # display progress
        hour, min, sec = hour_min_sec(timer() - t_start_c)
        print(f"\tFile completed in {hour} hour, {min} min, and {sec :0.1f} s")

    # display progress
    hour, min, sec = hour_min_sec(timer() - t_start)
    print(f"Total TFR analysis time: {hour} hour, {min} min, and {sec :0.1f} s")
     

def load_stats():
    # load stats
    fname = f"{PROJECT_PATH}/data/results/band_power_statistics.csv"
    df_stats = pd.read_csv(fname, index_col=0)
    df_stats = df_stats.loc[df_stats['memory']=='hit']

    # compute joint significance within material
    df_stats['sig_both'] = df_stats['alpha_sig'] & df_stats['gamma_sig'] # both bands within material
    df_stats['sig_either'] = df_stats['alpha_sig'] | df_stats['gamma_sig'] # either band within material

    # pivot table to compute joint significance across materials
    values = ['alpha_sig', 'gamma_sig', 'sig_either', 'sig_both']
    df_stats = df_stats.pivot_table(index=['patient', 'chan_idx'], 
                                    columns='material', values=values)
    df_stats.columns = [f"{col[0]}_{col[1]}" for col in df_stats.columns]
    df_stats.reset_index(inplace=True)
    for col in df_stats.columns[2:]:
        df_stats[col] = df_stats[col].astype(bool) # reset to booleen

    # compute joint significance across materials
    df_stats['sig_any'] = df_stats['sig_either_faces'] | \
                          df_stats['sig_either_words'] # either band, either material
    df_stats['sig_either_both'] = df_stats['sig_both_faces'] | \
                                  df_stats['sig_both_words'] # both band, either material
    df_stats['sig_all'] = df_stats['sig_both_faces'] & \
                          df_stats['sig_both_words'] # both band, both material
    
    return df_stats

if __name__ == "__main__":
    main()
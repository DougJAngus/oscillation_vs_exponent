"""
This script parameterizes the spectral results from 2_time_frequency_analysis.py

"""

# Imports
import os
import numpy as np
import pandas as pd
from specparam import SpectralGroupModel, SpectralTimeModel
from time import time as timer

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from info import N_JOBS, FREQ_RANGE, SPEC_PARAM_SETTINGS
from utils import hour_min_sec

# Settings
RUN_TFR = False # run TFR parameterization
N_SAMPLES = 2**7 # number of time samples after downsampling

# SpecParam hyperparameters
AP_MODE = ['knee'] # ['fixed', 'knee'] # aperiodic mode
FREQ_RANGE = [4, 100] # frequency range to fit
DECOMP_METHOD = 'tfr' # paraneterize PSDs or average TFRs
OVERWRITE = False # overwrite existing results

# This fixed the error: "Tcl_AsyncDelete: async handler deleted by the wrong thread"
import matplotlib
matplotlib.use('TkAgg')

def main():
    
    # parameterize PSDs
    print('\nParameterizing PSDs...')
    # param_group_psd_results()

    # parameterize TFRs
    if RUN_TFR:
        print('\nParameterizing TFRs...')
        parameterize_tfr()

def param_group_psd_results():
    # identify / create directories
    dir_input = f"{PROJECT_PATH}/data/ieeg_spectral_results"
    dir_output = f"{PROJECT_PATH}/data/ieeg_psd_specparam"
    if not os.path.exists(dir_output): 
        os.makedirs(f"{dir_output}/fooof_reports")
    
    # display progress
    t_start = timer()
    
    # loop through conditions
    files = [f for f in os.listdir(dir_input) if f.startswith(DECOMP_METHOD)]
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
            fg.save_report(f"{dir_output}/fooof_reports/{fname_out}")

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
    dir_output = f"{PROJECT_PATH}/data/ieeg_tfr_specparam"
    if not os.path.exists(f"{dir_output}/fooof_reports"): 
        os.makedirs(f"{dir_output}/fooof_reports")

    # load alpha/beta bandpower modulation results (resampling ananlysis)
    results = pd.read_csv(f"{PROJECT_PATH}/data/results/ieeg_modulated_channels.csv")
    df = results[results['sig']==1].reset_index(drop=True)
    
    # loop through significant channels
    for i_chan, row in df.iterrows():
        # get file name
        fname = f"{row['patient']}_{row['material']}_{row['memory']}" + \
            f"_chan{row['chan_idx']}_tfr.npz"

        # display progress
        print(f"    Analyzing file {i_chan}/{len(df)}") 
        print(f"\t{fname}")
        t_start_c = timer()
        
        # skip file is output already exists
        if not OVERWRITE:
            fname_out = fname.replace('.npz','_param_%s.json' %AP_MODE[0])
            if os.path.exists(f"{dir_output}/{fname_out}"):
                print("\t\tOutput already exists. Skipping...")
                continue

        # load tfr
        data_in = np.load(f"{dir_input}/{fname}")
        tfr_in = data_in['tfr']
        freq = data_in['freq']
        
        # average over trials
        tfr = np.squeeze(np.nanmean(tfr_in, axis=0))
        
        # parameterize
        for ap_mode in AP_MODE:
            # print(f"\t\tParameterizing with '{ap_mode}' aperiodic mode...")
            fg = SpectralTimeModel(**SPEC_PARAM_SETTINGS, aperiodic_mode=ap_mode, verbose=False)
            fg.set_check_modes(check_freqs=False, check_data=False)
            fg.fit(freq, tfr, n_jobs=N_JOBS, freq_range=FREQ_RANGE)
            
            # save results and report
            fname_out = fname.replace('.npz','_param_%s' %ap_mode)
            fg.save(f"{dir_output}/{fname_out}", save_results=True, 
                    save_settings=True)
            fg.save_report(f"{dir_output}/fooof_reports/{fname_out}")

        # display progress
        hour, min, sec = hour_min_sec(timer() - t_start_c)
        print(f"\tFile completed in {hour} hour, {min} min, and {sec :0.1f} s")

    # display progress
    hour, min, sec = hour_min_sec(timer() - t_start)
    print(f"Total TFR analysis time: {hour} hour, {min} min, and {sec :0.1f} s")
     
        
if __name__ == "__main__":
    main()
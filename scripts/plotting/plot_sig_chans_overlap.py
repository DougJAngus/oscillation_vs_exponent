"""
This script plots the results of scripts.3_id_modulated_channels.py, which
identifies channels wth significant modulation of alpha and/or gamma power.

"""

# Imports - standard
import os
import pandas as pd
import matplotlib.pyplot as plt

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from plots import plot_electrodes
from utils import combine_images
from settings import COLORS
    
# Plot settings
ELEC_SIZE = 24 # electrode size 
plt.style.use('mplstyle/default.mplstyle')

def main():

    # load results of step 3
    results = pd.read_csv(f"{PROJECT_PATH}/data/ieeg_stats/single_channel_stats_corr.csv", index_col=0)
    elec_pos = results[['pos_x', 'pos_y', 'pos_z']].values

    # loop through frequency bands
    for feature in ['alpha', 'gamma']:
        # display progress
        print(f"Plotting {feature} modulated channels...")

        # set/make directory for output figures
        dir_fig = f"{PROJECT_PATH}/figures/sig_chans_overlap/{feature}"
        if not os.path.exists(f"{dir_fig}"): 
            os.makedirs(f"{dir_fig}")

        # loop through hemispheres and views
        for hemisphere in ['right', 'left']:
            for view in ['lateral', 'medial']:
                # display progress
                print(f"\tPlotting {hemisphere} hemisphere, {view} view")

                # plot electrodes
                index = (results[f'{feature}_sig_corr']!=0) & \
                        (results[f'exponent_sig_corr']!=0)
                p = plot_electrodes(elec_pos[index], hemisphere, view,
                                    elec_color='r', elec_size=ELEC_SIZE, 
                                    return_plotter=True)

                index = (results[f'{feature}_sig_corr']!=0) & \
                        (results[f'exponent_sig_corr']==0)
                plot_electrodes(elec_pos[index], hemisphere, view,
                                    elec_color=COLORS['blue'], plotter=p,
                                    elec_size=ELEC_SIZE, return_plotter=True)

                index = (results[f'{feature}_sig_corr']==0) & \
                        (results[f'exponent_sig_corr']!=0)
                plot_electrodes(elec_pos[index], hemisphere, view,
                                    elec_color=COLORS['brown'], plotter=p,
                                    elec_size=ELEC_SIZE, return_plotter=True)
                                
                # save group plot for given hemisphere and view
                fname_out = f"{dir_fig}/{hemisphere}_hemisphere_{view}.png"
                p.screenshot(fname_out)

        # combine hemispheres and views into a single figure and save
        print("Combining hemispheres and views ")
        fname_out = f"{PROJECT_PATH}/figures/sig_chans_overlap/sig_chan_overlap_{feature}.png"
        combine_images(dir_fig, fname_out)

        # print results
        print("\nOverlap results:")
        print(f"\t{sum(results[f'{feature}_sig_corr']!=0)} channels with significant {feature} modulation")
        print(f"\t{sum(results[f'exponent_sig_corr']!=0)} channels with significant exponent modulation")
        print(f"\t{sum((results[f'{feature}_sig_corr']!=0) & (results[f'exponent_sig_corr']!=0))} channels with significant {feature} and exponent modulation")
        print(f"\t{sum((results[f'{feature}_sig_corr']!=0) & (results[f'exponent_sig_corr']==0))} channels with significant {feature} modulation only")
        print(f"\t{sum((results[f'{feature}_sig_corr']==0) & (results[f'exponent_sig_corr']!=0))} channels with significant exponent modulation only")
        print("\n\n")

        
if __name__ == "__main__":
    main()

"""
This script reproduces figure 3: Task-modulated electrodes. The results of 
scripts.3_id_modulated_channels.py are plotted.
A) Bar chart depicting percentage of task-modulated electrodes
B) Glass brain plot showing locations of task-modulated electrodes
C) Group mean power spectra for word block
D) Group mean power spectra for face block

"""

# Imports - standard
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from nilearn import plotting

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from info import MATERIALS
from plots import plot_spectra_2conditions, beautify_ax
from settings import COLORS, FREQ_RANGE, WIDTH, BCOLORS

# settings
plt.style.use('mplstyle/default.mplstyle')


def main():

    # make directory for output figures
    dir_fig = f"{PROJECT_PATH}/figures/main_figures"
    if not os.path.exists(dir_fig): 
        os.makedirs(dir_fig)

    # load electrode info
    fname_in = f"{PROJECT_PATH}/data/ieeg_metadata/ieeg_channel_info.csv"
    df = pd.read_csv(fname_in, index_col=0).drop(columns='index')

    # load results of step 3 and merge with electrode info
    fname = f"{PROJECT_PATH}/data/results/ieeg_modulated_channels.csv"
    temp = pd.read_csv(fname, index_col=0)
    df = df.merge(temp, on=['patient', 'chan_idx'])

    # create figure and gridspec
    fig = plt.figure(figsize=(WIDTH['2col'], WIDTH['2col']/4), 
                     constrained_layout=True)
    spec = gridspec.GridSpec(figure=fig, ncols=4, nrows=1,
                            width_ratios=[0.75, 2.75, 1, 1])
    axa = fig.add_subplot(spec[0,0])
    axb = fig.add_subplot(spec[0,1])
    axc = fig.add_subplot(spec[0,2])
    axd = fig.add_subplot(spec[0,3])

    # shift subplot spaceing (nilearn plot including inexplicable whitespace)
    boxb = axb.get_position()
    axb.set_position([boxb.x0 - 0.04, boxb.y0, boxb.width, boxb.height])
    
    # plot barchart: number of task-modulated electrodes
    x = [0, 1, 2]
    y = [df[col].sum() / len(df) * 100 for col in ['sig_alpha', 'sig_gamma', 'sig_all']] 
    axa.bar(x, y, color=[BCOLORS['alpha'], BCOLORS['gamma'], 'k'],
            edgecolor='black', linewidth=1, width=1)
    axa.set_xticks(x, labels=['alpha', 'gamma', 'both'])
    axa.set_ylabel('percentage (%)')
    axa.set_xlabel('frequency band')
    beautify_ax(axa)
    
    # plot glass brain: electrode locations
    df_ = df[df['sig_all']]
    nfig = plotting.plot_markers(node_coords=df_[['pos_x', 'pos_y', 'pos_z']].values, 
                        node_values=df_['sig_all'], node_size=2, colorbar=False, 
                        node_cmap='binary', node_vmin=0, node_vmax=1, 
                        display_mode='ortho', axes=axb, annotate=False)
    nfig.annotate(size=7) # must plot with annotate=False, then set size here

    df_alpha = df[(df['sig_alpha']) & (~df['sig_all'])]
    nfig.add_markers(marker_coords=df_alpha[['pos_x', 'pos_y', 'pos_z']].values, 
                     marker_size=1, marker_color=BCOLORS['alpha'])
    
    df_gamma = df[(df['sig_gamma']) & (~df['sig_all'])]
    nfig.add_markers(marker_coords=df_gamma[['pos_x', 'pos_y', 'pos_z']].values,
                        marker_size=1, marker_color=BCOLORS['gamma'])

    # plot spectra: group mean for word and face blocks
    plot_group_spectra(df, [axc, axd])

    # set titles
    axa.set_title("Task-modulated\nelectrode counts")
    axb.set_title("Task-modulated electrode locations")
    axc.set_title("\nword-encoding block")
    axd.set_title("\nface-encoding block")
    fig.text(0.8, 0.97, "             Mean power spectra", ha='center', va='center',
             fontsize=7)

    # save
    plt.savefig(f"{dir_fig}/figure_4")
    plt.savefig(f"{dir_fig}/figure_4.png")
    plt.close()


def plot_group_spectra(df, axes):

    for ax, material, color in zip(axes, MATERIALS, ['brown', 'blue']):
        # load data
        fname = f"{PROJECT_PATH}/data/ieeg_spectral_results/psd_{material}_hit_XXXstim.npz"
        data_pre = np.load(fname.replace("XXX", "pre"))
        data_post = np.load(fname.replace("XXX", "post"))
        psd_pre = data_pre['spectra'][df[f"sig_all"]]
        psd_post = data_post['spectra'][df[f"sig_all"]]
        freq = data_pre['freq']

        # plot
        # title = f"{material[0].upper()}{material[1:-1]} encoding"
        colors = [COLORS[f'light_{color}'], COLORS[color]]
        f_mask = np.logical_and(freq>FREQ_RANGE[0], freq<FREQ_RANGE[1])
        plot_spectra_2conditions(psd_pre[:, f_mask], psd_post[:, f_mask], 
                                freq[f_mask], shade_sem=True, ax=ax, 
                                color=colors)
        
        # beautify
        ax.grid(False)
        beautify_ax(ax)

        
if __name__ == "__main__":
    main()

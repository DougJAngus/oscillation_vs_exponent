"""
Plot results of scripts/step4_spectral_parameterization.py. For each feature of
interest, plot the distribution of values for the baseline and encoding period
as a violin and swarm plot, with 'split' and 'dodge' set to True. Also plot the
distribution of change in each feature between the baseline and encoding periods
as a histogram below the violin plot. 

"""

# Imports - standard
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.multitest import multipletests

# Imports - custom
import sys
sys.path.append("code")
from paths import PROJECT_PATH
from info import MATERIALS
from utils import get_start_time, print_time_elapsed
from plots import set_custom_colors
from specparam_utils import knee_freq
from settings import WIDTH

# settings
plt.style.use('mplstyle/default.mplstyle')
ALPHA = 0.05 # significance level
FEATURES = ['offset', 'knee', 'exponent', 'alpha', 'alpha_adj', 'gamma',
            'gamma_adj']
TITLES = ['Aperiodic offset', 'Aperiodic knee', 'Aperiodic exponent', 
          'Total alpha power', 'Adjusted alpha power', 'Total gamma power', 
            'Adjusted gamma power']
LABELS = ['offset (a.u.)', 'knee (Hz)', 'exponent', 'power (a.u.)',
            'power (a.u.)', 'power (a.u.)', 'power (a.u.)']


def main():

    # display progress
    t_start = get_start_time()

    # identify / create directories
    dir_output = f"{PROJECT_PATH}/figures/param_violin"
    if not os.path.exists(dir_output): 
        os.makedirs(f"{dir_output}")

    # load SpecParam results
    fname = f"{PROJECT_PATH}/data/results/spectral_parameters.csv"
    df = pd.read_csv(fname, index_col=0)
    df = df.loc[df['memory']=='hit'].reset_index(drop=True)
    df['knee'] = knee_freq(df['knee'], df['exponent']) # convert knee to Hz

    # get results for task-modulated channels
    fname = f"{PROJECT_PATH}/data/results/ieeg_modulated_channels.csv"
    temp = pd.read_csv(fname, index_col=0)
    df = df.merge(temp, on=['patient', 'chan_idx'])
    df = df.loc[df['sig_all']].reset_index(drop=True)

    # load group-level statistical results
    fname = f"{PROJECT_PATH}/data/ieeg_stats/group_level_hierarchical_bootstrap_active.csv"
    stats = pd.read_csv(fname, index_col=0)
    stats = stats.loc[stats['memory'] =='hit'].reset_index(drop=True)
    stats['p'] = stats['pvalue'].apply(lambda x: min(x, 1-x)) # standardize p-values (currently 0.5 represents equal and <0.05 and >0.95 are both significant)
    stats['p'].loc[stats['p']==0] = 0.001 # set p=0 to p=0.001
    mt = multipletests(stats['p'], alpha=0.05, method='holm')
    stats['p_corr'] = mt[1]
    
    # plot
    for feature, title, label in zip(FEATURES, TITLES, LABELS):
        fname_out = f"param_violin_{feature}.png"
        plot_contrasts_violin(df, stats, feature, title=title, y_label=label,
                                fname_out=f"{dir_output}/{fname_out}")

    # display progress
    print(f"\n\nTotal analysis time:")
    print_time_elapsed(t_start)


def plot_contrasts_violin(params, stats, y_var, title='', y_label=None, fname_out=None):
    # plot in each color
    set_custom_colors('browns')
    _plot_contrasts_violin(params, stats, y_var, title=title, y_label=y_label, 
                           loc='left', fname_out=fname_out.replace('.png', '_browns.png'))
    set_custom_colors('blues')
    _plot_contrasts_violin(params, stats, y_var, title=title, y_label=y_label, 
                           loc='right', fname_out=fname_out.replace('.png', '_blues.png'))

    # load each, crop, and join
    img_0 = plt.imread(fname_out.replace('.png', '_browns.png'))
    img_1 = plt.imread(fname_out.replace('.png', '_blues.png'))
    idx_mid = int(img_0.shape[1] * 0.55)
    image = np.concatenate([img_0[:, :idx_mid], img_1[:, idx_mid:]], axis=1)

    # plot combined image
    fig, ax = plt.subplots(figsize=[WIDTH['2col']/3, WIDTH['2col']/2])
    ax.imshow(image)
    ax.axis('off')

    # save
    if fname_out:
        fig.savefig(fname_out)
        plt.close('all')
    else:
        plt.show()
        
        
def _plot_contrasts_violin(params, stats, y_var, title='', y_label=None, 
                          fname_out=None, plot_swarm=True, loc='left'):
    # set plotting params
    plotting_params = {
        'data'  :   params,
        'x'     :   'material',
        'hue'   :   'epoch',
        'y'     :   y_var,
        'dodge' :   True,
        'split' :   True
    }

    # init
    if y_label is None:
        y_label = y_var.lower()

    # create figure

    fig = plt.figure(figsize=[WIDTH['2col']/3, WIDTH['2col']/2])
    gs = fig.add_gridspec(2,2, height_ratios=[2,1])
    ax1 = fig.add_subplot(gs[0,:])
    ax2l = fig.add_subplot(gs[1,0])
    ax2r = fig.add_subplot(gs[1,1])
    
    # ===== Upper Subplot =====
    # plot violin and swarm
    vp = sns.violinplot(**plotting_params, ax=ax1)
    if plot_swarm:
        plotting_params.pop('split')
        sns.swarmplot(**plotting_params, ax=ax1, size=2, 
                        palette='dark:#000000')

    # remove mean and quartile line
    for l in ax1.lines:
        l.set_linewidth(0)

    # Label
    ax1.set_title(title)
    vp.set_xlabel('')
    vp.set_ylabel(y_label)
    vp.set_xticks([0,1], labels=['word block','face block'])
    vp.xaxis.set_ticks_position('top')

    # add legend (and add space)
    handles, _ = vp.get_legend_handles_labels()
    if loc == 'left':
        vp.legend(handles=handles, labels=['baseline','encoding'],
                  bbox_to_anchor=(0.05, -0.1, 0.2, 0.1))
    elif loc == 'right':
        vp.legend(handles=handles, labels=['baseline','encoding'],
                  bbox_to_anchor=(0.82, -0.1, 0.2, 0.1))
        
    # connect paired data points on swarm plot
    params_p = params.pivot_table(index=['patient', 'chan_idx', 'material'],
                                    columns='epoch', values=y_var).reset_index()
    for i_mat, material in enumerate(MATERIALS):
        data = params_p.loc[params_p['material']==material, ['pre', 'post']]
        for i_chan in range(data.shape[0]):
            ax1.plot([-0.2+i_mat, 0.2+i_mat], data.iloc[i_chan], color='k', 
                     alpha=0.5, lw=0.5)

    # ===== Lower Subplot =====
    # plot disributions exponent change)
    df_p = params.pivot_table(index=['patient', 'chan_idx', 'material'], 
                              columns='epoch', values=y_var).reset_index()
    df_p['diff'] = df_p['post'] - df_p['pre']
    max_val = np.nanmax(np.abs(df_p['diff']))
    bins = np.linspace(-max_val, max_val, 21)
    for ax, material in zip([ax2l, ax2r], MATERIALS):
        diff = df_p.loc[df_p['material']==material, 'diff']
        ax.hist(diff, bins=bins, color='grey', label=material)
        ax.set(xlim=[-max_val, max_val])
        ax.set_xlabel(f"$\Delta$ {y_label}")
        # ax.set_ylabel('channel count')
        ax.axvline(0, color='k')
        ax.axvline(np.nanmean(diff), color='r', linestyle='--')

        # add stats
        if y_var == 'gamma_adj': # prevent overlap with other annotations - only gamma increases
            x_pos = 0.05
        else:
            x_pos = 0.55
        pval = stats.loc[((stats['material']==material) & 
                    (stats['feature']==y_var)), 'p_corr'].values
        if len(pval) == 1:
            if pval < 0.001:
                ax.text(x_pos, 0.85, f"*p<0.001", transform=ax.transAxes)
            elif pval < ALPHA:
                ax.text(x_pos, 0.85, f"*p={pval[0]:.3f}", transform=ax.transAxes)
            else:
                ax.text(x_pos, 0.85, f"p={pval[0]:.3f}", transform=ax.transAxes)
        else:
            print(f"Warning: missing or multiple p-values for '{y_var}' in {material} block")

    # adjust axis labels
    # ax2l.set_ylim([0, ax2l.get_ylim()[1]+1])
    ax2l.set_ylabel('channel count')
    ax2r.sharey(ax2l)
    for ax in [ax1, ax2l]:
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))

    # save figure
    if fname_out: 
        fig.savefig(fname_out)
        plt.close('all')
        
    return vp


if __name__ == "__main__":
    main()
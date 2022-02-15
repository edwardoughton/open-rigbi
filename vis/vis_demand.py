"""
Visualize demand data

Written by Ed Oughton.

April 2021.

"""
import os
import configparser
import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import contextily as ctx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS_FIGURES = os.path.join(BASE_PATH, '..', 'vis', 'figures')

def vis_maps(iso3, metric):
    """
    Visualize results.

    """
    filename = 'regional_annual_market_demand.csv'
    path = os.path.join(RESULTS, 'model_results', filename)
    data = pd.read_csv(path, encoding='utf8')
    data = data.loc[data['GID_0'] == iso3]

    data[metric[0]] = data[metric[0]] / data['area_km2']
    data[metric[1]] = data[metric[1]] / data['area_km2']

    data['f'] = pd.cut(data[metric[0]], metric[3], labels=metric[4])
    data['m'] = pd.cut(data[metric[1]], metric[3], labels=metric[4])

    filename = 'regions_2_{}.shp'.format(iso3)
    path = os.path.join(BASE_PATH, 'intermediate', iso3, 'regions')
    regions = gpd.read_file(os.path.join(path, filename), crs='epsg:4326', encoding='utf8')

    regions = pd.merge(left=regions, right=data, left_on='GID_2', right_on='GID_id')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    fig.suptitle(metric[2], fontsize=14, y=.8)

    regions.plot(column='f', categorical=True, cmap='Spectral_r', linewidth=.6,
        edgecolor='0.2', legend=False, legend_kwds={'ncol': 5}, ax=ax1)
    regions.plot(column='m', categorical=True, cmap='Spectral_r', linewidth=.6,
        edgecolor='0.2', legend=True, legend_kwds={'ncol': 5, 'loc':'lower center'}, ax=ax2)

    # ax1.axis('off')

    ax1.title.set_text('{}'.format('Female'))
    ax2.title.set_text('{}'.format('Male'))
    ctx.add_basemap(ax1, crs=regions.crs)
    ctx.add_basemap(ax2, crs=regions.crs)
    fig.subplots_adjust(wspace=-.2, hspace=-.5)

    leg = ax2.get_legend()
    leg.set_bbox_to_anchor((.6, -0.5, -0.2, 0))

    filename = '{}_{}.png'.format(metric[0], metric[1])
    plt.savefig(os.path.join(VIS_FIGURES, filename), pad_inches=0, dpi=100)
    plt.close()

    return print('Completed visualization')


def vis(iso3):
    """
    Visualize results.

    """
    filename = 'regional_annual_market_demand.csv'
    path = os.path.join(RESULTS, 'model_results', filename)
    data = pd.read_csv(path, encoding='utf8')
    data = data.loc[data['GID_0'] == iso3]
    data = data.loc[data['strategy'] == '3G_umts_wireless_srn_baseline_low_low']
    data = data.loc[data['confidence'] == 50]

    data['scenario'] = data['scenario'].map({
        'low_50_25_5': 'Low',
        'baseline_50_25_5': 'Baseline',
        'high_50_25_5': 'High'})

    data = data[['scenario', 'year',
        'population_with_phones_f_over_10', 'population_with_phones_m_over_10',
        'population_with_smartphones_f_over_10', 'population_with_smartphones_m_over_10',
    ]]

    data = data.groupby(['scenario', 'year'])[['population_with_phones_f_over_10',
        'population_with_phones_m_over_10',
        'population_with_smartphones_f_over_10',
        'population_with_smartphones_m_over_10']].agg('sum').reset_index()

    data.columns = ['Scenario', 'Year',
        'Phones (Female) (Aged >10 Years)',
        'Phones (Male) (Aged >10 Years)',
        'Smartphones (Female) (Aged >10 Years)',
        'Smartphones (Male) (Aged >10 Years)',
        ]

    long_data = pd.melt(data,
        id_vars=['Scenario', 'Year'],
        value_vars=['Phones (Female) (Aged >10 Years)',
        'Phones (Male) (Aged >10 Years)',
        'Smartphones (Female) (Aged >10 Years)',
        'Smartphones (Male) (Aged >10 Years)',])

    long_data.columns = ['Scenario', 'Year', 'Metric', 'Value']

    sns.set(font_scale=1.1)

    plot = sns.relplot(x="Year", y='Value', hue="Scenario",
        col="Metric", col_wrap=2, #palette=sns.color_palette("husl", 6),
        kind="line", data=long_data, hue_order=['Low', 'Baseline', 'High'],
        facet_kws=dict(sharex=False, sharey=False),
        legend="full")

    plot.fig.suptitle('Demand Forecasts 2020-2030', fontsize=16, y=1.025)

    handles = plot._legend_data.values()
    labels = plot._legend_data.keys()
    plot._legend.remove()
    plot.fig.legend(handles=handles, labels=labels, loc='lower center', ncol=7)

    plot.axes[0].set_ylabel('Cellphones')
    plot.axes[1].set_ylabel('Cellphones')
    plot.axes[2].set_ylabel('Smartphones')
    plot.axes[3].set_ylabel('Smartphones')

    plot.axes[0].set_xlabel('Year')
    plot.axes[1].set_xlabel('Year')
    plot.axes[2].set_xlabel('Year')
    plot.axes[3].set_xlabel('Year')

    plt.subplots_adjust(hspace=0.3, wspace=0.3, bottom=.1)

    filename = 'demand_forecasts.png'
    plot.savefig(os.path.join(VIS_FIGURES, filename), dpi=300)

    return print('Completed visualization')


if __name__ == '__main__':

    if not os.path.exists(VIS_FIGURES):
        os.makedirs(VIS_FIGURES)

    metrics = [
        (
            'population_f_over_10',
            'population_m_over_10',
            'Population Density (Persons Per Square Kilometer) (2020) (Aged >10 Years)',
            [0, 20, 30, 40, 50, 60, 70, 80, 90, 100, 10000],
            ['<20 $km^2$', '<30 $km^2$', '<40 $km^2$', '<50 $km^2$', '<60 $km^2$',
            '<70 $km^2$', '<80 $km^2$', '<90 $km^2$', '<100 $km^2$', '>100 $km^2$']
        ),
        (
            'population_with_phones_f_over_10',
            'population_with_phones_m_over_10',
            'Cellphone Density (Devices Per Square Kilometer) (2020) (Aged >10 Years)',
            [0, 20, 30, 40, 50, 60, 70, 80, 90, 100, 10000],
            ['<20 $km^2$', '<30 $km^2$', '<40 $km^2$', '<50 $km^2$', '<60 $km^2$',
            '<70 $km^2$', '<80 $km^2$', '<90 $km^2$', '<100 $km^2$', '>100 $km^2$']
        ),
        (
            'population_with_smartphones_f_over_10',
            'population_with_smartphones_m_over_10',
            'Smartphone Density (Smartphones Per Square Kilometer) (2020) (Aged >10 Years)',
            [0, 20, 30, 40, 50, 60, 70, 80, 90, 100, 10000],
            ['<20 $km^2$', '<30 $km^2$', '<40 $km^2$', '<50 $km^2$', '<60 $km^2$',
            '<70 $km^2$', '<80 $km^2$', '<90 $km^2$', '<100 $km^2$', '>100 $km^2$']
        ),
    ]

    # for metric in metrics:

    #     vis_maps('GMB', metric)

    vis('GMB')
